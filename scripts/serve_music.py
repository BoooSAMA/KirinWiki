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
from urllib.parse import unquote

MUSIC_DIR = Path(os.environ.get("MUSIC_DIR", "/home/cat/Music"))
PORT = int(os.environ.get("MUSIC_SERVER_PORT", "8765"))

MIME_MAP = {
    "mp3": "audio/mpeg",
    "flac": "audio/flac",
    "m4a": "audio/mp4",
    "ogg": "audio/ogg",
    "wav": "audio/wav",
    "ape": "audio/ape",
}


class MusicHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        # path 来自 HTTP 请求行，浏览器已做 URL 编码，需解码
        decoded = unquote(path)
        prefix = "/music/audio/"
        if decoded.startswith(prefix):
            rel = decoded[len(prefix):]
        elif decoded.startswith("/music/audio"):
            rel = decoded[len("/music/audio"):].lstrip("/")
        else:
            return str(MUSIC_DIR / decoded.lstrip("/"))

        target = str((MUSIC_DIR / rel).resolve())
        if not target.startswith(str(MUSIC_DIR.resolve())):
            return "/"
        return target

    def guess_type(self, path: str) -> str:
        ext = path.lower().rsplit(".", 1)[-1]
        return MIME_MAP.get(ext, "application/octet-stream")

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Range")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

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
