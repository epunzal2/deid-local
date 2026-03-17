from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import requests

from llm_local.core.health import probe_provider_health
from llm_local.core.llm_settings import load_runtime_settings


class _FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class _FakeSession:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses
        self.calls = 0

    def get(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
        self.calls += 1
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_probe_provider_health_retries_until_success() -> None:
    settings = load_runtime_settings(
        {
            "LLM_PROVIDER": "vllm",
            "VLLM_HEALTH_URL": "http://127.0.0.1:8001/healthz",
        }
    )
    session = _FakeSession(
        [
            requests.ConnectionError("unreachable"),
            _FakeResponse(status_code=503),
            _FakeResponse(status_code=200),
        ]
    )

    result = probe_provider_health(
        settings,
        wait_seconds=0.1,
        interval_seconds=0,
        session=session,
        sleep=lambda _seconds: None,
    )

    assert result.ok is True
    assert result.status_code == 200
    assert session.calls == 3


def test_probe_provider_health_returns_missing_model_for_llama_cpp(tmp_path: Path) -> None:
    settings = load_runtime_settings({})
    missing_path = tmp_path / "missing.gguf"
    settings = replace(settings, model_path=missing_path)

    result = probe_provider_health(settings)

    assert result.ok is False
    assert "not found" in result.message
