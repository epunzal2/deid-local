"""Environment-first runtime settings for LLM deployment surfaces."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ProviderName = Literal["llama_cpp", "openai_http", "vllm"]

DEFAULT_TEST_MODEL_PATH = Path("models/llm/Phi-3-mini-4k-instruct-q4.gguf")
DEFAULT_VLLM_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_VLLM_MODEL = "meta-llama/Llama-3-8B-Instruct"
DEFAULT_VLLM_HEALTH_URL = "http://127.0.0.1:8000/health"
DEFAULT_OPENAI_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_OPENAI_MODEL = "model"


@dataclass(frozen=True, slots=True)
class LLMSettingsOverrides:
    """Explicit runtime overrides, typically supplied by the CLI surface."""

    provider_name: str | None = None
    model_path: str | Path | None = None
    base_url: str | None = None
    model: str | None = None
    api_key: str | None = None
    health_url: str | None = None
    timeout_seconds: float | None = None
    max_retries: int | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    llama_ctx: int | None = None
    llama_gpu_layers: int | None = None
    llama_chat_format: str | None = None


@dataclass(frozen=True, slots=True)
class LLMRuntimeSettings:
    """Resolved settings for a concrete runtime backend."""

    provider_name: ProviderName
    model: str
    model_path: Path | None
    base_url: str | None
    api_key: str | None
    health_url: str | None
    timeout_seconds: float
    max_retries: int
    max_tokens: int | None
    temperature: float | None
    llama_ctx: int
    llama_gpu_layers: int
    llama_chat_format: str | None

    def sanitized_dict(self) -> dict[str, object]:
        """Return a JSON-serializable view without leaking credentials."""

        return {
            "provider_name": self.provider_name,
            "model": self.model,
            "model_path": str(self.model_path) if self.model_path is not None else None,
            "base_url": self.base_url,
            "api_key": "<redacted>" if self.api_key else None,
            "health_url": self.health_url,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "llama_ctx": self.llama_ctx,
            "llama_gpu_layers": self.llama_gpu_layers,
            "llama_chat_format": self.llama_chat_format,
        }


def load_runtime_settings(
    environ: Mapping[str, str] | None = None,
    *,
    overrides: LLMSettingsOverrides | None = None,
) -> LLMRuntimeSettings:
    """Resolve settings using CLI overrides, `DEID_*` vars, then legacy aliases."""

    env = environ if environ is not None else os.environ
    runtime_overrides = overrides or LLMSettingsOverrides()
    provider_name = _normalize_provider_name(
        runtime_overrides.provider_name
        or _first_value(env, "DEID_LLM_PROVIDER", "LLM_PROVIDER")
        or "llama_cpp"
    )
    timeout_seconds = _coerce_float(
        runtime_overrides.timeout_seconds,
        _first_value(env, "DEID_LLM_TIMEOUT_S"),
        default=30.0,
    )
    max_retries = _coerce_int(
        runtime_overrides.max_retries,
        _first_value(env, "DEID_LLM_MAX_RETRIES"),
        default=3,
    )
    max_tokens = _optional_int(
        runtime_overrides.max_tokens,
        _first_value(env, "DEID_LLM_MAX_TOKENS"),
    )
    temperature = _optional_float(
        runtime_overrides.temperature,
        _first_value(env, "DEID_LLM_TEMPERATURE"),
    )

    if provider_name == "llama_cpp":
        model_path = Path(
            str(
                runtime_overrides.model_path
                or _first_value(env, "DEID_LLAMA_MODEL_PATH", "LLAMA_CPP_MODEL_PATH")
                or DEFAULT_TEST_MODEL_PATH
            )
        )
        return LLMRuntimeSettings(
            provider_name=provider_name,
            model=model_path.name,
            model_path=model_path,
            base_url=None,
            api_key=None,
            health_url=None,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            max_tokens=max_tokens,
            temperature=temperature,
            llama_ctx=_coerce_int(
                runtime_overrides.llama_ctx,
                _first_value(env, "DEID_LLAMA_CTX"),
                default=4096,
            ),
            llama_gpu_layers=_coerce_int(
                runtime_overrides.llama_gpu_layers,
                _first_value(env, "DEID_LLAMA_GPU_LAYERS"),
                default=-1,
            ),
            llama_chat_format=runtime_overrides.llama_chat_format
            or _first_value(env, "DEID_LLAMA_CHAT_FORMAT"),
        )

    if provider_name == "openai_http":
        base_url = (
            runtime_overrides.base_url
            or _first_value(env, "DEID_OPENAI_BASE_URL")
            or DEFAULT_OPENAI_BASE_URL
        )
        health_url = (
            runtime_overrides.health_url
            or _first_value(env, "DEID_OPENAI_HEALTH_URL")
            or f"{base_url.rstrip('/')}/v1/models"
        )
        return LLMRuntimeSettings(
            provider_name=provider_name,
            model=(
                runtime_overrides.model
                or _first_value(env, "DEID_OPENAI_MODEL")
                or DEFAULT_OPENAI_MODEL
            ),
            model_path=None,
            base_url=base_url,
            api_key=runtime_overrides.api_key or _first_value(env, "DEID_OPENAI_API_KEY"),
            health_url=health_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            max_tokens=max_tokens,
            temperature=temperature,
            llama_ctx=4096,
            llama_gpu_layers=-1,
            llama_chat_format=None,
        )

    base_url = (
        runtime_overrides.base_url
        or _first_value(
            env,
            "DEID_VLLM_BASE_URL",
            "VLLM_BASE_URL",
        )
        or DEFAULT_VLLM_BASE_URL
    )
    health_url = runtime_overrides.health_url or _first_value(
        env,
        "DEID_VLLM_HEALTH_URL",
    )
    if health_url is None:
        legacy_health_port = _first_value(env, "VLLM_HEALTH_PORT")
        if legacy_health_port is not None:
            health_url = f"http://127.0.0.1:{legacy_health_port}/healthz"
        else:
            health_url = DEFAULT_VLLM_HEALTH_URL
    return LLMRuntimeSettings(
        provider_name="vllm",
        model=(
            runtime_overrides.model
            or _first_value(env, "DEID_VLLM_MODEL", "VLLM_MODEL")
            or DEFAULT_VLLM_MODEL
        ),
        model_path=None,
        base_url=base_url,
        api_key=runtime_overrides.api_key or _first_value(env, "DEID_VLLM_API_KEY", "VLLM_API_KEY"),
        health_url=health_url,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        max_tokens=max_tokens,
        temperature=temperature,
        llama_ctx=4096,
        llama_gpu_layers=-1,
        llama_chat_format=None,
    )


def _normalize_provider_name(value: str) -> ProviderName:
    normalized = value.strip().lower()
    aliases = {
        "llama_cpp": "llama_cpp",
        "llama-cpp": "llama_cpp",
        "openai_http": "openai_http",
        "openai": "openai_http",
        "vllm": "vllm",
        "vllm_api": "vllm",
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported LLM provider: {value}") from exc


def _first_value(environ: Mapping[str, str], *names: str) -> str | None:
    for name in names:
        value = environ.get(name)
        if value is not None and value != "":
            return value
    return None


def _coerce_int(primary: int | None, raw: str | None, *, default: int) -> int:
    if primary is not None:
        return primary
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _coerce_float(primary: float | None, raw: str | None, *, default: float) -> float:
    if primary is not None:
        return primary
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _optional_int(primary: int | None, raw: str | None) -> int | None:
    if primary is not None:
        return primary
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _optional_float(primary: float | None, raw: str | None) -> float | None:
    if primary is not None:
        return primary
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None
