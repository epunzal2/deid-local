from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from llm_local.adapters.llm import LLMRequest, build_provider
from llm_local.core.llm_settings import LLMSettingsOverrides, load_runtime_settings


class _ConcurrentMockOpenAIHandler(BaseHTTPRequestHandler):
    _required_api_key: str | None = None
    _lock = threading.Lock()
    _active_requests = 0
    _max_active_requests = 0

    @classmethod
    def reset_metrics(cls) -> None:
        with cls._lock:
            cls._active_requests = 0
            cls._max_active_requests = 0

    @classmethod
    def max_active_requests(cls) -> int:
        with cls._lock:
            return cls._max_active_requests

    def _is_authorized(self) -> bool:
        expected = self._required_api_key
        if expected is None:
            return True
        return self.headers.get("Authorization") == f"Bearer {expected}"

    def do_POST(self) -> None:  # noqa: N802
        if not self._is_authorized():
            self.send_response(401)
            self.end_headers()
            return
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return

        with self._lock:
            type(self)._active_requests += 1
            if type(self)._active_requests > type(self)._max_active_requests:
                type(self)._max_active_requests = type(self)._active_requests

        try:
            content_length = int(self.headers["Content-Length"])
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            prompt = payload["messages"][-1]["content"]
            # Force overlap so the test observes true concurrency.
            time.sleep(0.05)
            response = {"choices": [{"message": {"content": f"reply:{prompt}"}}]}
            body = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        finally:
            with self._lock:
                type(self)._active_requests -= 1

    def log_message(self, _format: str, *_args: object) -> None:
        return


@contextmanager
def _mock_openai_server(
    *,
    expected_api_key: str,
) -> Iterator[tuple[str, type[_ConcurrentMockOpenAIHandler]]]:
    handler_class = type(
        "ConfiguredConcurrentMockOpenAIHandler",
        (_ConcurrentMockOpenAIHandler,),
        {"_required_api_key": expected_api_key},
    )
    handler_class.reset_metrics()
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", handler_class
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def _infer_once(base_url: str, prompt: str, api_key: str) -> str:
    settings = load_runtime_settings(
        overrides=LLMSettingsOverrides(
            provider_name="openai_http",
            base_url=base_url,
            model="mock-model",
            api_key=api_key,
            timeout_seconds=5.0,
            max_retries=2,
        )
    )
    provider = build_provider(settings)
    response = provider.infer(LLMRequest(prompt=prompt))
    return response.text


def test_concurrent_openai_http_requests() -> None:
    api_key = "token-123"
    prompts = [f"ping-{index}" for index in range(24)]

    with _mock_openai_server(expected_api_key=api_key) as (base_url, handler_class):
        with ThreadPoolExecutor(max_workers=8) as pool:
            replies = list(pool.map(lambda prompt: _infer_once(base_url, prompt, api_key), prompts))

    expected_replies = [f"reply:{prompt}" for prompt in prompts]
    assert sorted(replies) == sorted(expected_replies)
    assert handler_class.max_active_requests() >= 2
