from __future__ import annotations

from llm_local.adapters.llm.base import LLMRequest
from llm_local.adapters.llm.factory import build_provider
from llm_local.adapters.llm.llama_cpp import LlamaCppProvider
from llm_local.adapters.llm.openai_http import OpenAICompatibleProvider, VLLMProvider
from llm_local.core.llm_settings import load_runtime_settings


class _FakeLlamaClient:
    def create_chat_completion(self, *, messages, **_kwargs):  # type: ignore[no-untyped-def]
        return {
            "choices": [
                {
                    "message": {
                        "content": f"echo:{messages[-1]['content']}",
                    }
                }
            ]
        }


def test_build_provider_dispatches_expected_types() -> None:
    llama_provider = build_provider(load_runtime_settings({}))
    openai_provider = build_provider(load_runtime_settings({"LLM_PROVIDER": "openai_http"}))
    vllm_provider = build_provider(load_runtime_settings({"LLM_PROVIDER": "vllm"}))

    assert isinstance(llama_provider, LlamaCppProvider)
    assert isinstance(openai_provider, OpenAICompatibleProvider)
    assert isinstance(vllm_provider, VLLMProvider)


def test_llama_provider_can_use_injected_client_without_optional_dependency() -> None:
    settings = load_runtime_settings({})
    provider = LlamaCppProvider(settings, client=_FakeLlamaClient())

    response = provider.infer(LLMRequest(prompt="ping"))

    assert response.text == "echo:ping"
    assert response.provider_name == "llama_cpp"
