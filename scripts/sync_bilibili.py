#!/usr/bin/env python3
"""
sync_bilibili.py — 从 Bilibili 收藏夹同步音频到本地

用法:
  # 查看收藏夹信息（不下载）
  python scripts/sync_bilibili.py --info

  # 下载全部
  python scripts/sync_bilibili.py --media-id 4057903921

  # 下载，只处理未下载的（跳过已有文件）
  python scripts/sync_bilibili.py --media-id 4057903921 --skip-existing

  # 下载后自动运行 sync_music.py 刷新歌单
  python scripts/sync_bilibili.py --media-id 4057903921 --sync

工作流程:
  1. 从 Bilibili API 获取收藏夹列表
  2. 检查分 P 视频，拆分多个音频
  3. 下载音频到 /home/cat/Music/bilibili/{BV号}/
  4. 清理已不在收藏夹内的旧文件
  5. 可选：运行 sync_music.py 刷新歌单

元数据覆盖:
  编辑 data/music/local.json，按 BV 号覆盖自动抓取的歌名/歌手：
  {
    "bilibili": {
      "BV1xx...": {
        "p1": { "name": "正确歌名", "artist": "歌手名" },
        "p2": { "name": "另一首歌", "artist": "歌手名" }
      }
    }
  }
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

import requests

# 配置
MUSIC_DIR = Path(os.environ.get("MUSIC_DIR", "/home/cat/Music"))
BILIBILI_DIR = MUSIC_DIR / "bilibili"
LOCAL_OVERRIDES = Path(__file__).resolve().parent.parent / "data" / "music" / "local.json"
SYNC_SCRIPT = Path(__file__).resolve().parent / "sync_music.py"

# 分 P 命名正则：文件名中的 (1) (2) 等是 B 站下载默认添加的，需要清理
PAGE_SUFFIX_RE = re.compile(r"\s*\(\d+\)\s*$")

# API 基础 URL
API_BASE = "https://api.bilibili.com"
# HEADERS — 模拟浏览器
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}

# ========== 辅助函数 ==========

def clean_bilibili_title(title: str) -> str:
    """清理 B 站视频标题中的修饰文字"""
    # 去掉 【xxx】 标签
    title = re.sub(r"【[^】]*】", "", title)
    # 去掉各种 [] 标签
    title = re.sub(r"\[[^\]]*\]", "", title)
    # 去掉 "4K" "Hi-Res" "HiRes" "无损" "整轨" 等关键词
    for kw in ["无损", "整轨", "Hi-Res", "HiRes", "HiFi", "4K", "60帧", "歌词版", "音质好到超乎想象"]:
        title = title.replace(kw, "")
    # 合并多余空格和特殊字符
    title = re.sub(r"\s+", " ", title)
    title = re.sub(r"[|｜:：]", " ", title)
    title = title.strip().strip("-").strip()
    return title


def extract_artist_album(title: str, uploader: str) -> tuple[str, str]:
    """从标题和上传者提取歌手和专辑名"""
    # 尝试匹配《专辑名》
    album_match = re.search(r"[《（(]\s*(.+?)\s*[）)》]", title)
    album = album_match.group(1) if album_match else ""

    # 尝试匹配歌手名（在专辑名前）
    if album_match:
        before_album = title[: album_match.start()].strip()
        artist_match = re.search(r"([\u4e00-\u9fff\w]+)", before_album)
        artist = artist_match.group(1) if artist_match else uploader
    else:
        artist = uploader

    # 清理标题作为歌名
    name = clean_bilibili_title(title)
    if album and name.endswith(album):
        name = name[: -len(album)].strip()
    name = re.sub(r"\s+", " ", name).strip().strip("-").strip() or title[:30]

    return artist, album, name


# ========== Bilibili API ==========

def get_fav_list(media_id: str, page: int = 1, page_size: int = 20) -> dict:
    """获取收藏夹内容"""
    r = requests.get(
        f"{API_BASE}/x/v3/fav/resource/list",
        params={
            "media_id": media_id,
            "pn": page,
            "ps": page_size,
            "platform": "web",
        },
        headers=HEADERS,
        timeout=15,
    )
    return r.json()


def get_video_info(bvid: str) -> dict:
    """获取视频详情（含分 P 信息）"""
    r = requests.get(
        f"{API_BASE}/x/web-interface/view",
        params={"bvid": bvid},
        headers=HEADERS,
        timeout=15,
    )
    return r.json()


def get_audio_url(bvid: str, cid: int) -> str | None:
    """获取音频下载 URL"""
    r = requests.get(
        f"{API_BASE}/x/player/playurl",
        params={
            "bvid": bvid,
            "cid": cid,
            "qn": 0,
            "platform": "web",
            "fnval": 4048,
            "fnver": 0,
            "fourk": 1,
        },
        headers=HEADERS,
        timeout=15,
    )
    d = r.json()
    if d.get("code") != 0:
        return None

    audio_list = d.get("data", {}).get("dash", {}).get("audio", [])
    if not audio_list:
        return None
    best = max(audio_list, key=lambda x: x.get("bandwidth", 0))
    return best["baseUrl"]


# ========== 下载 ==========

def download_audio(url: str, dest: Path) -> bool:
    """下载音频并转成 M4A"""
    dest.parent.mkdir(parents=True, exist_ok=True)

    # 如果已存在且大小 > 1KB，跳过
    if dest.exists() and dest.stat().st_size > 1024:
        return True

    temp = dest.with_suffix(dest.suffix + ".tmp")
    try:
        r = requests.get(url, headers=HEADERS, timeout=120, stream=True)
        r.raise_for_status()
        with open(temp, "wb") as f:
            downloaded = 0
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
            if downloaded < 1024:
                temp.unlink(missing_ok=True)
                return False
    except Exception as e:
        temp.unlink(missing_ok=True)
        return False

    # 下载的 m4s 文件需要 ffmpeg 转成标准 m4a
    m4a_dest = dest.with_suffix(".m4a")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(temp), "-c", "copy", "-f", "mp4", str(m4a_dest)],
            capture_output=True,
            timeout=120,
        )
        if m4a_dest.exists() and m4a_dest.stat().st_size > 1024:
            temp.unlink(missing_ok=True)
            # 重命名 .m4a 为 .m4a（已经是 m4a 了）
            # 但实际上 dest 可能期望 .m4a 或 .mp3
            # 如果 dest 后缀不是 .m4a，重命名
            if dest.suffix != ".m4a":
                os.rename(m4a_dest, dest)
            return True
        else:
            temp.unlink(missing_ok=True)
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # ffmpeg 不可用时回退：直接改名
        os.rename(temp, dest)
        return dest.exists() and dest.stat().st_size > 1024


def process_video(media: dict, overrides: dict) -> dict | None:
    """处理单个收藏项"""
    bvid = media.get("bv_id", "")
    if not bvid:
        return None

    print(f"\n  📹 BV: {bvid}")
    print(f"     {media.get('title', '?')[:80]}")

    # 获取视频详情
    info = get_video_info(bvid)
    if info.get("code") != 0:
        print(f"  ⚠  API 错误: {info.get('message', '未知')}")
        return None

    data = info["data"]
    uploader = data.get("owner", {}).get("name", "未知UP主")
    pages = data.get("pages", [])
    video_title = data.get("title", "")

    artist, album, name = extract_artist_album(video_title, uploader)

    results = []

    for page in pages:
        pid = page["page"]
        part = page.get("part", "")
        cid = page["cid"]

        # 文件名：BV号 + 分P
        if len(pages) > 1:
            subdir = BILIBILI_DIR / bvid / f"p{pid:02d}"
            display_name = part or f"{name} P{pid}"
        else:
            subdir = BILIBILI_DIR / bvid
            display_name = name or video_title

        # 应用手动覆盖
        override = overrides.get(bvid, {}).get(f"p{pid}", {})
        final_name = override.get("name", display_name)
        final_artist = override.get("artist", artist)
        final_album = override.get("album", album)

        # 文件名处理
        safe_name = re.sub(r'[\\/:*?"<>|]', "", final_name).strip()
        audio_file = subdir / f"{safe_name}.m4a"
        info_file = subdir / "info.json"

        # 获取音频 URL
        audio_url = get_audio_url(bvid, cid)
        if not audio_url:
            print(f"  ⚠  无法获取音频链接 (P{pid})")
            continue

        # 下载
        skip = audio_file.exists() and audio_file.stat().st_size > 1024
        if not skip:
            print(f"  ⬇  下载: {final_name}")
            ok = download_audio(audio_url, audio_file)
            if not ok:
                print(f"  ❌  下载失败: {final_name}")
                continue
            time.sleep(1)  # 请求间隔
        else:
            print(f"  ✓  已存在: {final_name}")

        # 写入 info.json
        info_data = {
            "bvid": bvid,
            "page": pid,
            "source": "bilibili",
            "title": final_name,
            "artist": final_artist,
            "album": final_album,
            "uploader": uploader,
            "url": f"https://www.bilibili.com/video/{bvid}",
        }
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(info_data, f, ensure_ascii=False, indent=2)

        results.append({
            "bvid": bvid,
            "page": pid,
            "file": audio_file,
            "name": final_name,
            "artist": final_artist,
            "album": final_album,
        })

    return {"bvid": bvid, "results": results}


def cleanup_removed(current_bvids: set[str]):
    """删除已不在收藏夹中的旧文件"""
    if not BILIBILI_DIR.exists():
        return

    for item in BILIBILI_DIR.iterdir():
        if not item.is_dir():
            continue
        bvid = item.name
        if bvid not in current_bvids:
            import shutil
            shutil.rmtree(item)
            print(f"  🗑  已清理: {bvid}")


# ========== 主函数 ==========

def load_overrides() -> dict:
    """加载手动元数据覆盖"""
    if LOCAL_OVERRIDES.exists():
        with open(LOCAL_OVERRIDES, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("bilibili", {})
    return {}


def show_info(media_id: str):
    """只显示收藏夹信息，不下载"""
    r = get_fav_list(media_id, page=1, page_size=20)
    if r.get("code") != 0:
        print(f"❌ API 错误: {r.get('message', '未知')}")
        return

    data = r["data"]
    info = data.get("info", {})
    medias = data.get("medias", [])
    total = info.get("media_count", len(medias))

    print(f"\n📁 收藏夹: {info.get('title', '?')}")
    print(f"   共 {total} 个视频\n")

    for m in medias:
        bv = m.get("bv_id", "?")
        title = m.get("title", "?")
        upper = m.get("upper", {}).get("name", "?")
        print(f"  {bv} | {upper} | {title[:60]}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="从 Bilibili 收藏夹同步音频")
    parser.add_argument("--media-id", default="4057903921", help="收藏夹 media_id")
    parser.add_argument("--info", action="store_true", help="只显示信息不下载")
    parser.add_argument("--skip-existing", action="store_true", help="跳过已下载")
    parser.add_argument("--sync", action="store_true", help="完成后运行 sync_music.py")
    parser.add_argument("--cookie", help="B站 Cookie（可选，用于更高音质）")
    args = parser.parse_args()

    if args.cookie:
        HEADERS["Cookie"] = args.cookie

    if args.info:
        show_info(args.media_id)
        return

    # 获取收藏夹全量列表
    print(f"📋 获取收藏夹: {args.media_id}")
    all_medias = []
    page = 1
    while True:
        r = get_fav_list(args.media_id, page=page)
        if r.get("code") != 0:
            print(f"❌ API 错误: {r.get('message', '未知')}")
            sys.exit(1)
        data = r["data"]
        medias = data.get("medias", [])
        all_medias.extend(medias)
        total = data.get("info", {}).get("media_count", 0)
        if len(all_medias) >= total:
            break
        page += 1
        time.sleep(0.5)

    print(f"  共 {len(all_medias)} 个视频\n")

    overrides = load_overrides()
    current_bvids = set()

    for media in all_medias:
        bvid = media.get("bv_id", "")
        if bvid:
            current_bvids.add(bvid)
        result = process_video(media, overrides)
        if result:
            for r in result.get("results", []):
                print(f"     → {r['artist']} — {r['name']}")

    # 清理已移除的
    cleanup_removed(current_bvids)

    # 可选：运行 sync_music.py 刷新歌单
    if args.sync:
        print("\n🔄 刷新本地歌单...")
        subprocess.run([sys.executable, str(SYNC_SCRIPT)])
    else:
        print(f"\n✅ 完成！运行 `python scripts/sync_music.py` 即可刷新歌单")

    return 0


if __name__ == "__main__":
    sys.exit(main())
