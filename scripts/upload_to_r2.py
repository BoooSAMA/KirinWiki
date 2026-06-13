#!/usr/bin/env python3
"""
upload_to_r2.py — 将本地音乐上传到 Cloudflare R2

用法:
  # 设置 R2 凭证（或写入 .env）
  export R2_ACCOUNT_ID="你的 Account ID"
  export R2_ACCESS_KEY_ID="你的 R2 Access Key"
  export R2_ACCESS_KEY_SECRET="你的 R2 Secret Key"

  # 扫描音乐目录并上传
  python scripts/upload_to_r2.py

  # 指定桶名
  python scripts/upload_to_r2.py --bucket my-custom-name

  # 不真的上传，只预览要上传的文件
  python scripts/upload_to_r2.py --dry-run

需要:
  - boto3 (pip install --break-system-packages boto3)
  - R2 已在 Cloudflare Dashboard 激活
  - R2 API Token (Dashboard → R2 → 管理 API 令牌 → 创建令牌)
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

import boto3
from botocore.config import Config

# 配置
MUSIC_DIR = Path(os.environ.get("MUSIC_DIR", "/home/cat/Music"))
PROJECT_DIR = Path(__file__).resolve().parent.parent
SYNC_SCRIPT = PROJECT_DIR / "scripts" / "sync_music.py"
R2_PLAYLIST = PROJECT_DIR / "public" / "music" / "playlist.r2.json"
MUSIC_EXTS = {".mp3", ".flac", ".m4a", ".ogg", ".wav", ".ape"}

# R2 配置（从环境变量读取，或 .env 文件）
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID", "")
R2_ACCESS_KEY_SECRET = os.environ.get("R2_ACCESS_KEY_SECRET", "")
R2_BUCKET = os.environ.get("R2_BUCKET", "music-store")
R2_PUBLIC_URL = os.environ.get("R2_PUBLIC_URL", "")

# 上传并发数
MAX_WORKERS = 4


def load_local_playlist() -> list[dict]:
    """从本地 sync_music.py 输出的 playlist.json 加载"""
    path = PROJECT_DIR / "public" / "music" / "playlist.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def scan_music_dir() -> list[Path]:
    """直接扫描 MUSIC_DIR 获取所有音频文件"""
    files = []
    for f in sorted(MUSIC_DIR.rglob("*")):
        if f.is_file() and f.suffix.lower() in MUSIC_EXTS:
            files.append(f)
    return files


def get_r2_key(filepath: Path) -> str:
    """生成 R2 中的对象键（保持与本地一致的相对路径）"""
    return str(filepath.relative_to(MUSIC_DIR))


def upload_file(s3, bucket: str, filepath: Path, dry_run: bool) -> dict:
    """上传单个文件到 R2，返回结果"""
    key = get_r2_key(filepath)
    size = filepath.stat().st_size

    if dry_run:
        return {"key": key, "size": size, "status": "dry-run"}

    try:
        content_type = _guess_type(filepath)
        s3.upload_file(
            str(filepath), bucket, key,
            ExtraArgs={"ContentType": content_type},
        )
        return {"key": key, "size": size, "status": "ok"}
    except Exception as e:
        return {"key": key, "size": size, "status": "error", "error": str(e)}


def _guess_type(filepath: Path) -> str:
    ext = filepath.suffix.lower()
    return {
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".wav": "audio/wav",
    }.get(ext, "application/octet-stream")


def get_r2_client():
    """创建 R2 S3 客户端"""
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_ACCESS_KEY_SECRET]):
        print("❌ R2 凭证未设置。请设置环境变量:")
        print("   export R2_ACCOUNT_ID='你的 Account ID'")
        print("   export R2_ACCESS_KEY_ID='你的 R2 Access Key'")
        print("   export R2_ACCESS_KEY_SECRET='你的 R2 Secret Key'")
        sys.exit(1)

    endpoint = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_ACCESS_KEY_SECRET,
        config=Config(signature_version="s3v4"),
    )


def generate_public_url(key: str) -> str:
    """生成公开可访问的 R2 URL"""
    if R2_PUBLIC_URL:
        # 使用自定义域名
        return f"{R2_PUBLIC_URL.rstrip('/')}/{quote(key, safe='/')}"
    else:
        # 使用 r2.dev 子域名
        return f"/music/audio/{quote(key, safe='/')}"


def update_playlist_json(uploaded: list[dict]):
    """更新 playlist.r2.json，使用 R2 公开 URL"""
    local_songs = load_local_playlist()
    uploaded_keys = {u["key"] for u in uploaded if u["status"] == "ok"}

    r2_songs = []
    for song in local_songs:
        # 从 URL 提取相对路径
        url = song.get("url", "")
        if "/music/audio/" in url:
            key = url.split("/music/audio/", 1)[1]
            from urllib.parse import unquote
            key = unquote(key)
        else:
            continue

        if key in uploaded_keys:
            r2_songs.append({
                "name": song["name"],
                "artist": song["artist"],
                "url": generate_public_url(key),
                "cover": song.get("cover", ""),
            })
        else:
            # 未上传的歌曲保留本地 URL（在 R2 JSON 中放本地路径）
            r2_songs.append(song)

    R2_PLAYLIST.parent.mkdir(parents=True, exist_ok=True)
    with open(R2_PLAYLIST, "w", encoding="utf-8") as f:
        json.dump(r2_songs, f, ensure_ascii=False, indent=2)

    print(f"📄 写入 R2 歌单: {R2_PLAYLIST} ({len(r2_songs)} 首)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="上传本地音乐到 Cloudflare R2")
    parser.add_argument("--bucket", default=R2_BUCKET, help="R2 桶名")
    parser.add_argument("--dry-run", action="store_true", help="只预览不上传")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="并发数")
    args = parser.parse_args()

    print(f"🔍 扫描: {MUSIC_DIR}")
    files = scan_music_dir()
    if not files:
        print("❌ 未找到音频文件")
        sys.exit(1)
    print(f"  找到 {len(files)} 个文件")

    if args.dry_run:
        print(f"\n📋 预览 (不上传):")
        total = 0
        for f in files:
            size = f.stat().st_size
            key = get_r2_key(f)
            total += size
            print(f"  {key} ({size/1024/1024:.1f}MB)")
        print(f"\n总计: {len(files)} 文件, {total/1024/1024:.1f}MB")
        return

    # 上传
    s3 = get_r2_client()
    print(f"\n⬆  上传到 R2 桶: {args.bucket}")

    uploaded = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(upload_file, s3, args.bucket, f, False): f for f in files}
        done = 0
        total = len(futures)
        for future in as_completed(futures):
            done += 1
            result = future.result()
            uploaded.append(result)
            status_sym = "✓" if result["status"] == "ok" else "✗"
            size_mb = result["size"] / 1024 / 1024
            print(f"  [{done}/{total}] {status_sym} {result['key']} ({size_mb:.1f}MB)")

    # 统计
    ok = sum(1 for u in uploaded if u["status"] == "ok")
    err = sum(1 for u in uploaded if u["status"] == "error")
    total_size = sum(u["size"] for u in uploaded if u["status"] == "ok")
    print(f"\n✅ 完成: {ok} 上传成功, {err} 失败, {total_size/1024/1024:.1f}MB")

    # 生成 R2 歌单
    update_playlist_json(uploaded)
    print(f"🎵 现在可以在生产环境使用 R2 歌单了")


if __name__ == "__main__":
    main()
