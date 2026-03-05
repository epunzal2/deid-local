"""Command-line entry points for deid-local."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from deid_local.adapters.llm import LLMRequest, build_provider
from deid_local.core.health import probe_provider_health
from deid_local.core.llm_settings import (
    DEFAULT_TEST_MODEL_PATH,
    LLMSettingsOverrides,
    load_runtime_settings,
)
from deid_local.core.runtime import build_runtime_summary, format_runtime_summary
from deid_local.utils.model_assets import download_model_asset, verify_model_asset


def _run_doctor(_args: argparse.Namespace) -> int:
    summary = build_runtime_summary()
    print(format_runtime_summary(summary))
    return 0


def _run_llm_config(args: argparse.Namespace) -> int:
    try:
        settings = _load_llm_settings(args)
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(settings.sanitized_dict(), indent=2, sort_keys=True))
    return 0


def _run_llm_health(args: argparse.Namespace) -> int:
    try:
        settings = _load_llm_settings(args)
        result = probe_provider_health(
            settings,
            wait_seconds=args.wait_seconds,
            interval_seconds=args.interval_seconds,
        )
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    output = sys.stdout if result.ok else sys.stderr
    print(result.message, file=output)
    return 0 if result.ok else 1


def _run_llm_infer(args: argparse.Namespace) -> int:
    try:
        settings = _load_llm_settings(args)
        provider = build_provider(settings)
        response = provider.infer(
            LLMRequest(
                prompt=args.prompt,
                system_prompt=args.system,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
            )
        )
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(response.text)
    return 0


def _run_model_fetch(args: argparse.Namespace) -> int:
    try:
        model_path = download_model_asset(
            repo_id=args.repo_id,
            filename=args.filename,
            output_dir=args.output_dir,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(model_path)
    return 0


def _run_model_verify(args: argparse.Namespace) -> int:
    model_path = verify_model_asset(args.path)
    if model_path is None:
        print(f"Model file not found: {args.path}", file=sys.stderr)
        return 1
    print(f"Model file exists: {model_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deid-local",
        description=(
            "Utilities for developing local-first LLM workflows that can later run on "
            "Linux HPC GPUs."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Print a runtime summary for local or HPC execution contexts.",
    )
    doctor_parser.set_defaults(handler=_run_doctor)

    llm_common = _build_llm_common_parser()
    llm_parser = subparsers.add_parser("llm", help="Inspect and exercise LLM runtimes.")
    llm_parser.set_defaults(handler=_make_help_handler(llm_parser))
    llm_subparsers = llm_parser.add_subparsers(dest="llm_command")

    llm_config_parser = llm_subparsers.add_parser(
        "config",
        parents=[llm_common],
        help="Print resolved and sanitized LLM runtime settings.",
    )
    llm_config_parser.set_defaults(handler=_run_llm_config)

    llm_health_parser = llm_subparsers.add_parser(
        "health",
        parents=[llm_common],
        help="Validate a local model path or probe a remote provider health endpoint.",
    )
    llm_health_parser.add_argument(
        "--wait-seconds",
        type=float,
        default=45.0,
        help="Maximum time to wait for a passing health probe.",
    )
    llm_health_parser.add_argument(
        "--interval-seconds",
        type=float,
        default=5.0,
        help="Delay between health probe attempts.",
    )
    llm_health_parser.set_defaults(handler=_run_llm_health)

    llm_infer_parser = llm_subparsers.add_parser(
        "infer",
        parents=[llm_common],
        help="Run a one-shot inference request against the selected provider.",
    )
    llm_infer_parser.add_argument(
        "--prompt",
        required=True,
        help="Prompt text to send to the provider.",
    )
    llm_infer_parser.add_argument(
        "--system",
        help="Optional system prompt to prepend to the request.",
    )
    llm_infer_parser.set_defaults(handler=_run_llm_infer)

    model_parser = subparsers.add_parser("model", help="Fetch or verify local model assets.")
    model_parser.set_defaults(handler=_make_help_handler(model_parser))
    model_subparsers = model_parser.add_subparsers(dest="model_command")

    model_fetch_parser = model_subparsers.add_parser(
        "fetch",
        help="Download a test model or other GGUF artifact from Hugging Face.",
    )
    model_fetch_parser.add_argument(
        "--repo-id",
        default="microsoft/Phi-3-mini-4k-instruct-gguf",
        help="Hugging Face repository ID.",
    )
    model_fetch_parser.add_argument(
        "--filename",
        default=DEFAULT_TEST_MODEL_PATH.name,
        help="Filename to download from the repository.",
    )
    model_fetch_parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_TEST_MODEL_PATH.parent),
        help="Directory where the model should be stored.",
    )
    model_fetch_parser.set_defaults(handler=_run_model_fetch)

    model_verify_parser = model_subparsers.add_parser(
        "verify",
        help="Check whether a local model asset exists.",
    )
    model_verify_parser.add_argument(
        "--path",
        default=str(DEFAULT_TEST_MODEL_PATH),
        help="Path to the model asset that should exist.",
    )
    model_verify_parser.set_defaults(handler=_run_model_verify)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)


def _build_llm_common_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--provider",
        choices=["llama_cpp", "openai_http", "vllm"],
        help="Provider to resolve instead of the environment default.",
    )
    parser.add_argument(
        "--model-path",
        help="Override the local GGUF model path when using `llama_cpp`.",
    )
    parser.add_argument(
        "--base-url",
        help="Override the base URL for HTTP-backed providers.",
    )
    parser.add_argument(
        "--model",
        help="Override the remote model identifier for HTTP-backed providers.",
    )
    parser.add_argument(
        "--health-url",
        help="Override the health endpoint for HTTP-backed providers.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        help="Override the HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        help="Override the HTTP retry budget.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        help="Override the output token cap.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        help="Override the request temperature.",
    )
    parser.add_argument(
        "--llama-ctx",
        type=int,
        help="Override the llama.cpp context window size.",
    )
    parser.add_argument(
        "--llama-gpu-layers",
        type=int,
        help="Override the number of GPU layers for llama.cpp.",
    )
    parser.add_argument(
        "--llama-chat-format",
        help="Override the llama.cpp chat format when needed.",
    )
    return parser


def _load_llm_settings(args: argparse.Namespace):
    return load_runtime_settings(overrides=_build_llm_overrides(args))


def _build_llm_overrides(args: argparse.Namespace) -> LLMSettingsOverrides:
    return LLMSettingsOverrides(
        provider_name=getattr(args, "provider", None),
        model_path=getattr(args, "model_path", None),
        base_url=getattr(args, "base_url", None),
        model=getattr(args, "model", None),
        health_url=getattr(args, "health_url", None),
        timeout_seconds=getattr(args, "timeout_seconds", None),
        max_retries=getattr(args, "max_retries", None),
        max_tokens=getattr(args, "max_tokens", None),
        temperature=getattr(args, "temperature", None),
        llama_ctx=getattr(args, "llama_ctx", None),
        llama_gpu_layers=getattr(args, "llama_gpu_layers", None),
        llama_chat_format=getattr(args, "llama_chat_format", None),
    )


def _make_help_handler(parser: argparse.ArgumentParser):
    def _handler(_args: argparse.Namespace) -> int:
        parser.print_help()
        return 0

    return _handler
