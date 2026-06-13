#!/usr/bin/env python3
"""
serve_music.py — 本地开发时提供音频文件

用法:  python scripts/serve_music.py

在 8765 端口启动 HTTP 服务，把 /music/audio/... 请求映射到 MUSIC_DIR。
Astro dev server 通过 Vite proxy 将 /music/audio/* 转发至此服务。

与 sync_music.py 配合使用，sync 生成的 JSON 中 URL 以 /music/audio/ 开头，
开发时实际文件由此服务提供。
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

MUSIC_DIR = Path(os.environ.get("MUSIC_DIR", "/home/cat/Music"))
PORT = int(os.environ.get("MUSIC_SERVER_PORT", "8765"))


class MusicHandler(SimpleHTTPRequestHandler):
    """将请求路径 /music/audio/Artist/Album/File 映射到 MUSIC_DIR/Artist/Album/File"""

    def translate_path(self, path: str) -> str:
        # 期望路径如 /music/audio/艺术家/专辑/文件
        # 去掉 /music/audio/ 前缀
        prefix = "/music/audio/"
        if path.startswith(prefix):
            rel = path[len(prefix):]
        elif path.startswith("/music/audio"):
            rel = path[len("/music/audio"):].lstrip("/")
        else:
            return str(MUSIC_DIR / path.lstrip("/"))

        target = str((MUSIC_DIR / rel).resolve())
        # 安全检查：必须在 MUSIC_DIR 内
        if not target.startswith(str(MUSIC_DIR.resolve())):
            return "/"
        return target

    def log_message(self, format, *args):
        print(f"[music] {self.address_string()} - {format % args}", file=sys.stderr)


def main():
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    server = HTTPServer(("127.0.0.1", PORT), MusicHandler)
    print(f"🎵 音乐服务器: http://127.0.0.1:{PORT}")
    print(f"   映射: /music/audio/ → {MUSIC_DIR}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  已停止")
        server.server_close()


if __name__ == "__main__":
    main()
