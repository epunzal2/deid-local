"""`llama.cpp` provider implementation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from deid_local.adapters.llm.base import LLMProvider, LLMRequest, LLMResponse


class LlamaCppProvider(LLMProvider):
    """Adapter for a local `llama-cpp-python` runtime."""

    def __init__(
        self,
        settings,
        *,
        client: Any | None = None,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        super().__init__(settings)
        self._client = client
        self._client_factory = client_factory

    def infer(self, request: LLMRequest) -> LLMResponse:
        client = self._get_client()
        response = self._invoke_client(client, request)
        return LLMResponse(
            text=_extract_text(response),
            provider_name=self.provider_name,
            model=self.settings.model,
            raw=response,
        )

    def _get_client(self) -> Any:
        if self._client is None:
            client_factory = self._client_factory or _import_llama_factory()
            kwargs: dict[str, object] = {
                "model_path": str(self.settings.model_path),
                "n_ctx": self.settings.llama_ctx,
                "n_gpu_layers": self.settings.llama_gpu_layers,
                "verbose": False,
            }
            if self.settings.llama_chat_format:
                kwargs["chat_format"] = self.settings.llama_chat_format
            self._client = client_factory(**kwargs)
        return self._client

    def _invoke_client(self, client: Any, request: LLMRequest) -> Any:
        max_tokens = request.max_tokens or self.settings.max_tokens or 256
        temperature = (
            request.temperature if request.temperature is not None else self.settings.temperature
        )
        kwargs: dict[str, object] = {"max_tokens": max_tokens}
        if temperature is not None:
            kwargs["temperature"] = temperature
        if request.stop:
            kwargs["stop"] = list(request.stop)
        if hasattr(client, "create_chat_completion"):
            messages: list[dict[str, str]] = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
            return client.create_chat_completion(messages=messages, **kwargs)
        if callable(client):
            return client(_render_prompt(request), echo=False, **kwargs)
        raise RuntimeError("Configured llama.cpp client does not support inference.")


def _extract_text(response: Any) -> str:
    choices = response.get("choices") if isinstance(response, dict) else None
    if choices:
        first_choice = choices[0]
        message = first_choice.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content.strip()
        text = first_choice.get("text")
        if isinstance(text, str):
            return text.strip()
    return str(response).strip()


def _render_prompt(request: LLMRequest) -> str:
    prompt_sections: list[str] = []
    if request.system_prompt:
        prompt_sections.append(f"System:\n{request.system_prompt.strip()}")
    prompt_sections.append(f"User:\n{request.prompt.strip()}")
    prompt_sections.append("Assistant:")
    return "\n\n".join(prompt_sections)


def _import_llama_factory() -> Callable[..., Any]:
    try:
        from llama_cpp import Llama
    except ImportError as exc:  # pragma: no cover - exercised via runtime behavior
        raise RuntimeError(
            "llama-cpp-python is not installed. Install the optional `llama_cpp` extra."
        ) from exc
    return Llama
