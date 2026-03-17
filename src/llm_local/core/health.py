"""Health helpers for local and remote LLM runtimes."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import requests

from llm_local.core.llm_settings import LLMRuntimeSettings


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    """Structured health-check response for CLI rendering and tests."""

    ok: bool
    provider_name: str
    target: str
    message: str
    status_code: int | None = None


def probe_provider_health(
    settings: LLMRuntimeSettings,
    *,
    wait_seconds: float = 45.0,
    interval_seconds: float = 5.0,
    session: requests.Session | object | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> HealthCheckResult:
    """Check a local model path or retry an HTTP probe until the deadline."""

    if settings.provider_name == "llama_cpp":
        return validate_model_path(settings)

    target = settings.health_url or "<unset>"
    requester = session or requests.Session()
    deadline = time.monotonic() + max(wait_seconds, 0.0)
    last_message = f"Health probe failed for {target}"
    last_status_code: int | None = None

    while True:
        try:
            response = requester.get(
                target,
                headers=_build_headers(settings),
                timeout=settings.timeout_seconds,
            )
            last_status_code = response.status_code
            if response.status_code < 400:
                return HealthCheckResult(
                    ok=True,
                    provider_name=settings.provider_name,
                    target=target,
                    message=f"Health probe succeeded for {target}",
                    status_code=response.status_code,
                )
            last_message = f"Health probe returned HTTP {response.status_code} for {target}"
        except requests.RequestException as exc:
            last_message = f"Health probe failed for {target}: {exc}"

        if time.monotonic() >= deadline:
            return HealthCheckResult(
                ok=False,
                provider_name=settings.provider_name,
                target=target,
                message=last_message,
                status_code=last_status_code,
            )
        sleep(max(interval_seconds, 0.0))


def validate_model_path(settings: LLMRuntimeSettings) -> HealthCheckResult:
    """Validate that the configured local model path exists."""

    model_path = settings.model_path or Path("<unset>")
    if settings.model_path is not None and settings.model_path.exists():
        return HealthCheckResult(
            ok=True,
            provider_name=settings.provider_name,
            target=str(model_path),
            message=f"Model file exists: {model_path}",
        )
    return HealthCheckResult(
        ok=False,
        provider_name=settings.provider_name,
        target=str(model_path),
        message=f"Model file not found: {model_path}",
    )


def _build_headers(settings: LLMRuntimeSettings) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"
    return headers
