"""Dependency-free local web demo for notices, digest and cited Q&A."""

from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .classifier import classify
from .io import read_notices
from .retriever import BM25Index, answer


ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "web"


def serve(data_path: str | Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    notices = read_notices(data_path)
    index = BM25Index(notices)
    rows = [
        {
            **{
                key: value
                for key, value in notice.to_dict().items()
                if key not in {"gold_category", "gold_market_impacting", "label_status"}
            },
            "prediction": classify(notice).to_dict(),
        }
        for notice in notices
    ]

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'self'; script-src 'self'; "
                "img-src 'self' data:; connect-src 'self'",
            )
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/api/notices":
                body = json.dumps(rows, ensure_ascii=False).encode("utf-8")
                self._send(200, body, "application/json; charset=utf-8")
                return
            if parsed.path == "/api/ask":
                question = parse_qs(parsed.query).get("q", [""])[0].strip()
                if not question or len(question) > 300:
                    body = json.dumps(
                        {"error": "question must contain 1-300 characters"}, ensure_ascii=False
                    ).encode("utf-8")
                    self._send(400, body, "application/json; charset=utf-8")
                    return
                body = json.dumps(answer(index, question), ensure_ascii=False).encode("utf-8")
                self._send(200, body, "application/json; charset=utf-8")
                return
            requested = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
            path = (WEB_DIR / requested).resolve()
            if WEB_DIR.resolve() not in path.parents or not path.is_file():
                self._send(404, b"not found", "text/plain")
                return
            guessed, _ = mimetypes.guess_type(path.name)
            content_type = f"{guessed or 'application/octet-stream'}; charset=utf-8"
            self._send(200, path.read_bytes(), content_type)

        def log_message(self, fmt: str, *args: object) -> None:
            print(f"[demo] {fmt % args}")

    print(f"Power Notice Radar running at http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
