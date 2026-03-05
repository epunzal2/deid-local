"""Factory for LLM provider adapters."""

from __future__ import annotations

from deid_local.adapters.llm.base import LLMProvider
from deid_local.adapters.llm.llama_cpp import LlamaCppProvider
from deid_local.adapters.llm.openai_http import OpenAICompatibleProvider, VLLMProvider
from deid_local.core.llm_settings import LLMRuntimeSettings


def build_provider(settings: LLMRuntimeSettings) -> LLMProvider:
    """Construct the appropriate adapter for the resolved runtime settings."""

    if settings.provider_name == "llama_cpp":
        return LlamaCppProvider(settings)
    if settings.provider_name == "openai_http":
        return OpenAICompatibleProvider(settings)
    if settings.provider_name == "vllm":
        return VLLMProvider(settings)
    raise ValueError(f"Unsupported LLM provider: {settings.provider_name}")
