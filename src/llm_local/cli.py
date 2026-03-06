"""Command-line entry points for llm-local."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from collections.abc import Sequence
from pathlib import Path

from llm_local.adapters.llm import LLMRequest, build_provider
from llm_local.core.chat_service import create_chat_app
from llm_local.core.endpoint_discovery import read_endpoint, resolve_endpoint_dir
from llm_local.core.health import probe_provider_health
from llm_local.core.llm_settings import (
    DEFAULT_TEST_MODEL_PATH,
    LLMSettingsOverrides,
    load_runtime_settings,
)
from llm_local.core.runtime import build_runtime_summary, format_runtime_summary
from llm_local.utils.model_assets import (
    download_hf_snapshot,
    download_model_asset,
    verify_model_asset,
)


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


def _run_llm_chat(args: argparse.Namespace) -> int:
    try:
        settings = _load_llm_settings(args)
        provider = build_provider(settings)
        app = create_chat_app(
            provider,
            system_prompt=args.system,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Starting chat server at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)
    return 0


def _run_llm_connect(args: argparse.Namespace) -> int:
    endpoint_dir: Path | None
    if args.endpoint_dir:
        endpoint_dir = Path(args.endpoint_dir).expanduser()
    else:
        endpoint_dir = resolve_endpoint_dir()
    if endpoint_dir is None:
        print(
            "VLLM endpoint directory is not configured. Use --endpoint-dir or set "
            "VLLM_ENDPOINT_DIR.",
            file=sys.stderr,
        )
        return 1

    try:
        endpoint = read_endpoint(endpoint_dir)
    except (OSError, ValueError) as exc:
        print(f"Failed to read endpoint metadata: {exc}", file=sys.stderr)
        return 1
    if endpoint is None:
        print(f"Endpoint file not found: {endpoint_dir / 'vllm-endpoint.json'}", file=sys.stderr)
        return 1

    base_url = args.base_url or endpoint.base_url
    health_url = args.health_url or endpoint.health_url
    model = args.model or endpoint.model
    api_key = args.api_key

    print(f"export LLM_PROVIDER={shlex.quote('vllm')}")
    print(f"export VLLM_ENDPOINT_DIR={shlex.quote(str(endpoint_dir))}")
    print(f"export VLLM_BASE_URL={shlex.quote(base_url)}")
    print(f"export VLLM_HEALTH_URL={shlex.quote(health_url)}")
    print(f"export VLLM_MODEL={shlex.quote(model)}")
    if api_key:
        print(f"export VLLM_API_KEY={shlex.quote(api_key)}")
    elif endpoint.api_key_required:
        print(
            "# Endpoint requires authentication; set VLLM_API_KEY before health/infer.",
            file=sys.stderr,
        )

    if not args.test:
        return 0

    settings = load_runtime_settings(
        overrides=LLMSettingsOverrides(
            provider_name="vllm",
            base_url=base_url,
            model=model,
            api_key=api_key,
            health_url=health_url,
        )
    )
    result = probe_provider_health(
        settings,
        wait_seconds=args.wait_seconds,
        interval_seconds=args.interval_seconds,
    )
    output = sys.stdout if result.ok else sys.stderr
    print(result.message, file=output)
    return 0 if result.ok else 1


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


def _run_model_fetch_hf(args: argparse.Namespace) -> int:
    token = args.token or os.environ.get("HF_TOKEN") or None
    try:
        model_path = download_hf_snapshot(
            repo_id=args.repo_id,
            output_dir=args.output_dir,
            token=token,
            revision=args.revision,
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
        prog="llm-local",
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

    llm_chat_parser = llm_subparsers.add_parser(
        "chat",
        parents=[llm_common],
        help="Start a local browser chat window for smoke testing.",
    )
    llm_chat_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface for the local chat server.",
    )
    llm_chat_parser.add_argument(
        "--port",
        type=int,
        default=8088,
        help="Port for the local chat server.",
    )
    llm_chat_parser.add_argument(
        "--system",
        help="Optional system prompt to prepend to each chat request.",
    )
    llm_chat_parser.set_defaults(handler=_run_llm_chat)

    llm_connect_parser = llm_subparsers.add_parser(
        "connect",
        parents=[llm_common],
        help="Read a shared vLLM endpoint file and print export commands.",
    )
    llm_connect_parser.add_argument(
        "--endpoint-dir",
        help="Directory containing vllm-endpoint.json. Defaults to VLLM_ENDPOINT_DIR.",
    )
    llm_connect_parser.add_argument(
        "--test",
        action="store_true",
        help="Run a health probe against the resolved endpoint after printing exports.",
    )
    llm_connect_parser.add_argument(
        "--wait-seconds",
        type=float,
        default=30.0,
        help="Maximum time to wait for a passing health probe when --test is set.",
    )
    llm_connect_parser.add_argument(
        "--interval-seconds",
        type=float,
        default=2.0,
        help="Delay between health probe attempts when --test is set.",
    )
    llm_connect_parser.set_defaults(handler=_run_llm_connect)

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

    model_fetch_hf_parser = model_subparsers.add_parser(
        "fetch-hf",
        help="Download a full Hugging Face snapshot for vLLM serving.",
    )
    model_fetch_hf_parser.add_argument(
        "--repo-id",
        required=True,
        help="Hugging Face repository ID to download.",
    )
    model_fetch_hf_parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where the model snapshot should be stored.",
    )
    model_fetch_hf_parser.add_argument(
        "--token",
        help="Optional Hugging Face access token. Falls back to HF_TOKEN.",
    )
    model_fetch_hf_parser.add_argument(
        "--revision",
        help="Optional git revision, branch, or tag.",
    )
    model_fetch_hf_parser.set_defaults(handler=_run_model_fetch_hf)

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
        "--api-key",
        help="Override the API key used for HTTP-backed providers.",
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
        api_key=getattr(args, "api_key", None),
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
