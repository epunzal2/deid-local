"""Base types for LLM adapter implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from llm_local.core.llm_settings import LLMRuntimeSettings


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """Normalized one-shot inference request."""

    prompt: str
    system_prompt: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    stop: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Normalized inference response."""

    text: str
    provider_name: str
    model: str
    raw: Any = field(default=None, repr=False)


class LLMProvider(ABC):
    """Minimal provider interface shared by all adapters."""

    def __init__(self, settings: LLMRuntimeSettings) -> None:
        self.settings = settings

    @property
    def provider_name(self) -> str:
        return self.settings.provider_name

    @abstractmethod
    def infer(self, request: LLMRequest) -> LLMResponse:
        """Execute a single prompt against the configured provider."""
