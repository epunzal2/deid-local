from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from deid_local.cli import main


class _MockOpenAIHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return
        if self.path == "/v1/models":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"data":[]}')
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return
        content_length = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        prompt = payload["messages"][-1]["content"]
        response = {
            "choices": [
                {
                    "message": {
                        "content": f"reply:{prompt}",
                    }
                }
            ]
        }
        body = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


@contextmanager
def _mock_openai_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _MockOpenAIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_llm_health_works_against_mock_http_server(capsys) -> None:
    with _mock_openai_server() as base_url:
        exit_code = main(
            [
                "llm",
                "health",
                "--provider",
                "openai_http",
                "--base-url",
                base_url,
                "--health-url",
                f"{base_url}/health",
                "--wait-seconds",
                "0.1",
                "--interval-seconds",
                "0",
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "succeeded" in captured.out


def test_llm_infer_works_against_mock_http_server(capsys) -> None:
    with _mock_openai_server() as base_url:
        exit_code = main(
            [
                "llm",
                "infer",
                "--provider",
                "openai_http",
                "--base-url",
                base_url,
                "--model",
                "mock-model",
                "--prompt",
                "ping",
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "reply:ping"
