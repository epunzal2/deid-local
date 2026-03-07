"""OpenAI-compatible HTTP provider implementations."""

from __future__ import annotations

import time
from typing import Any

import requests

from llm_local.adapters.llm.base import LLMProvider, LLMRequest, LLMResponse


class OpenAICompatibleProvider(LLMProvider):
    """Adapter for OpenAI-compatible chat completion endpoints."""

    def __init__(self, settings, *, session: requests.Session | None = None) -> None:
        super().__init__(settings)
        self._session = session or requests.Session()

    def infer(self, request: LLMRequest) -> LLMResponse:
        payload = self._build_payload(request)
        last_exc: Exception | None = None

        for attempt in range(1, self.settings.max_retries + 1):
            try:
                response = self._session.post(
                    self._completion_url,
                    headers=self._headers(),
                    json=payload,
                    timeout=self.settings.timeout_seconds,
                )
                if response.status_code >= 400:
                    detail = response.text[:300]
                    raise ValueError(
                        f"HTTP {response.status_code} returned by {self._completion_url}: {detail}"
                    )
                data = response.json()
                return LLMResponse(
                    text=_extract_message_text(data),
                    provider_name=self.provider_name,
                    model=self.settings.model,
                    raw=data,
                )
            except (requests.RequestException, ValueError) as exc:
                last_exc = exc
                if attempt == self.settings.max_retries:
                    break
                time.sleep(min(2 ** (attempt - 1), 5))

        assert last_exc is not None
        raise RuntimeError(
            f"Completion request failed for {self._completion_url}: {last_exc}"
        ) from last_exc

    @property
    def _completion_url(self) -> str:
        assert self.settings.base_url is not None
        return f"{self.settings.base_url.rstrip('/')}/v1/chat/completions"

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"
        return headers

    def _build_payload(self, request: LLMRequest) -> dict[str, Any]:
        temperature = (
            request.temperature if request.temperature is not None else self.settings.temperature
        )
        max_tokens = request.max_tokens or self.settings.max_tokens
        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        payload: dict[str, Any] = {
            "model": self.settings.model,
            "messages": messages,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if request.stop:
            payload["stop"] = list(request.stop)
        return payload


class VLLMProvider(OpenAICompatibleProvider):
    """Named subclass used when the resolved provider is `vllm`."""


def _extract_message_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices", [])
    if not choices:
        raise ValueError("No choices returned from completion endpoint.")
    message = choices[0].get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "".join(item.get("text", "") for item in content if isinstance(item, dict)).strip()
    text = choices[0].get("text")
    if isinstance(text, str):
        return text.strip()
    raise ValueError("Unable to extract completion text from response payload.")
