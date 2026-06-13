#!/usr/bin/env python3
"""
sync_music.py — 扫描本地音乐文件夹，生成 APlayer 歌单 JSON + 创建音频软链

用法:
  python scripts/sync_music.py

配置:
  MUSIC_DIR  = 本地音乐文件夹（默认 /home/cat/Music）
  OUTPUT_DIR = 项目中的 public/music（Astro dev server 直接服务此目录）

输出:
  public/music/playlist.json  — APlayer 可用歌单
  public/music/audio/...      — 指向原始音频的软链接

结构支持:
  Artist/Album/Anything.mp3   — 标准两级目录
  总结/Song.mp3               — 散装歌曲
"""

import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

MUSIC_DIR = Path(os.environ.get("MUSIC_DIR", "/home/cat/Music"))
PROJECT_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = PROJECT_DIR / "public" / "music"
PLAYLIST_FILE = PUBLIC_DIR / "playlist.json"

SUPPORTED_EXTS = {".mp3", ".flac", ".m4a", ".ogg", ".wav", ".ape"}

# ============ 元数据读取 ============
def read_metadata(filepath: Path) -> dict:
    """用 mutagen 读取音频元数据，回退到文件名解析"""
    meta = {"title": "", "artist": "", "album": ""}

    try:
        ext = filepath.suffix.lower()
        if ext == ".flac":
            from mutagen.flac import FLAC
            audio = FLAC(filepath)
        elif ext == ".mp3":
            from mutagen.mp3 import EasyMP3
            audio = EasyMP3(filepath)
        elif ext == ".m4a":
            from mutagen.mp4 import MP4
            audio = MP4(filepath)
            # MP4 用不同 key
            tags = {}
            if audio.tags:
                for key, val in audio.tags.items():
                    if key.startswith("\xa9"):
                        tags[key] = val
            meta["title"] = tags.get("\xa9nam", [""])[0]
            meta["artist"] = tags.get("\xa9ART", [""])[0]
            meta["album"] = tags.get("\xa9alb", [""])[0]
            return meta
        else:
            meta["title"] = ""
            meta["artist"] = ""
            meta["album"] = ""

        if hasattr(audio, "tags") and audio.tags:
            meta["title"] = str(audio.get("title", [""])[0])
            meta["artist"] = str(audio.get("artist", [""])[0])
            meta["album"] = str(audio.get("album", [""])[0])
    except Exception:
        pass

    return meta


def parse_filename(filepath: Path) -> dict:
    """从文件名回退解析 artist 和 title"""
    stem = filepath.stem
    artist = ""
    title = ""

    # Pattern: "Artist - Title" or "Artist - Title (suffix)"
    if " - " in stem:
        parts = stem.split(" - ", 1)
        artist = parts[0].strip()
        title = parts[1].strip()
        # 清理 "(1)"、"(Remix)" 等后缀
        for suffix in [" (1)", " (2)", " (3)"]:
            if title.endswith(suffix):
                title = title[: -len(suffix)]
                break
    else:
        # Pattern: "TrackNo.Title-Artist" (如林忆莲)
        title = stem

    # 去掉开头的序号 "1." "01." "10."
    import re
    title = re.sub(r"^\d+\.\s*", "", title).strip()
    # 去掉末尾 " -Artist"
    if artist:
        title = title.rstrip()

    return {"title": title or stem, "artist": artist}


def get_relative_artist(filepath: Path) -> str:
    """从文件路径中提取艺术家名（MUSIC_DIR 下第一级目录）"""
    rel = filepath.relative_to(MUSIC_DIR)
    parts = rel.parts
    if len(parts) >= 2:
        return parts[0]
    return "未知"


def get_relative_album(filepath: Path) -> str:
    """从文件路径中提取专辑名（MUSIC_DIR 下第二级目录）"""
    rel = filepath.relative_to(MUSIC_DIR)
    parts = rel.parts
    if len(parts) >= 3:
        return parts[1]
    elif len(parts) == 2:
        return parts[0]  # 散装歌曲，用父目录名
    return ""


# ============ 扫描 ============
def scan_music() -> list[dict]:
    """扫描 MUSIC_DIR，返回 [{source, rel_path, meta}]"""
    entries = []

    for f in sorted(MUSIC_DIR.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix.lower() not in SUPPORTED_EXTS:
            continue

        # 读取元数据
        meta = read_metadata(f)
        if not meta["title"]:
            # fallback: 文件名解析
            parsed = parse_filename(f)
            meta["title"] = parsed["title"]
            if not meta["artist"]:
                meta["artist"] = parsed["artist"] or get_relative_artist(f)
        if not meta["artist"]:
            meta["artist"] = get_relative_artist(f)
        if not meta["album"]:
            meta["album"] = get_relative_album(f)

        # 用实际文件系统路径（server 和 R2 都映射此路径）
        actual_path = f.relative_to(MUSIC_DIR)

        entries.append({
            "source": f,
            "actual_path": actual_path,
            "artist": meta["artist"],
            "album": meta["album"],
            "name": meta["title"],
        })

    return entries


def generate_json(entries: list[dict]):
    playlist = []
    for entry in entries:
        posix_path = entry["actual_path"].as_posix()
        url_path = quote(posix_path, safe="/")
        playlist.append({
            "name": entry["name"],
            "artist": entry["artist"],
            "url": f"/music/audio/{url_path}",
            "cover": "",
        })
    return playlist


def main():
    print(f"🔍 扫描: {MUSIC_DIR}")
    entries = scan_music()

    if not entries:
        print("❌ 未找到音频文件")
        sys.exit(1)

    print(f"  找到 {len(entries)} 个音频文件")

    playlist = generate_json(entries)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(playlist, f, ensure_ascii=False, indent=2)
    print(f"📄 写入歌单: {PLAYLIST_FILE} ({len(playlist)} 首)")

    # 打印预览
    print(f"\n🎵 歌单预览:")
    for s in playlist[:10]:
        print(f"  {s['artist']} — {s['name']}")
    if len(playlist) > 10:
        print(f"  ... 等 {len(playlist)} 首")

    return 0


if __name__ == "__main__":
    sys.exit(main())
