#!/usr/bin/env python3
"""
deploy.py — 一键部署完整流程：
  1. sync_music    — 扫描本地音乐生成歌单
  2. upload_to_r2  — 上传新歌到 R2（如有凭证）
  3. build         — npm run build
  4. deploy        — npx wrangler deploy
  5. git commit    — 提交更新的歌单 JSON（可选）

用法:
  # 更新音乐 + 部署
  python scripts/deploy.py

  # 只更新歌单 + 构建（不上传 R2、不部署）
  python scripts/deploy.py --skip-upload --skip-deploy

  # 从 .env 读取 R2 凭证
  python scripts/deploy.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


def log(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def run(cmd, cwd=None):
    print(f"  $ {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=cwd or PROJECT)
    if r.returncode != 0:
        print(f"  ❌ 失败 (exit={r.returncode})")
        sys.exit(r.returncode)
    return r


def check_credentials():
    """检查是否有 R2 上传凭证"""
    return all([
        os.environ.get("R2_ACCESS_KEY_ID"),
        os.environ.get("R2_ACCESS_KEY_SECRET"),
        os.environ.get("R2_ACCOUNT_ID"),
    ])


def main():
    import argparse
    parser = argparse.ArgumentParser(description="一键部署音乐博客")
    parser.add_argument("--skip-sync", action="store_true", help="跳过扫描音乐")
    parser.add_argument("--skip-upload", action="store_true", help="跳过上传 R2")
    parser.add_argument("--skip-build", action="store_true", help="跳过构建")
    parser.add_argument("--skip-deploy", action="store_true", help="跳过部署")
    parser.add_argument("--commit", action="store_true", help="完成后 git commit + push")
    parser.add_argument("--no-env", action="store_true", help="不从 .env 加载")
    args = parser.parse_args()

    # 尝试从 .env 加载凭证
    env_file = PROJECT / ".env"
    if not args.no_env and env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    has_creds = check_credentials()

    # 环境信息
    print(f"📁 项目: {PROJECT}")
    print(f"🔑 R2 凭证: {'✅ 有' if has_creds else '❌ 无（跳过上传）'}")

    # Step 1: 扫描音乐 → playlist.json
    if not args.skip_sync:
        log("Step 1/4: 扫描音乐")
        run(f"{sys.executable} scripts/sync_music.py")
    else:
        print("⏭  跳过扫描")

    # Step 2: 上传新歌到 R2
    if not args.skip_upload and has_creds:
        log("Step 2/4: 上传 R2")
        r2_public = os.environ.get("R2_PUBLIC_URL", "https://music.myproxy2.cc.cd")
        run(f'{sys.executable} scripts/upload_to_r2.py --bucket music-store', cwd=PROJECT)
    else:
        print("⏭  跳过上传 R2")

    # Step 3: 构建
    if not args.skip_build:
        log("Step 3/4: 构建")
        run("npm run build")
    else:
        print("⏭  跳过构建")

    # Step 4: 部署
    if not args.skip_deploy:
        log("Step 4/4: 部署到 Cloudflare")
        run("npx wrangler deploy")
    else:
        print("⏭  跳过部署")

    # 可选：git 提交
    if args.commit:
        log("Git commit + push")
        run("git add public/music/playlist.json public/music/playlist.r2.json")
        run('git commit -m "chore: 更新歌单" --allow-empty')
        run("git push")

    print(f"\n{'='*60}")
    print(f"  ✅ 完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
