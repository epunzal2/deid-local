"""Command-line entry points for deid-local."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from deid_local.core.runtime import build_runtime_summary, format_runtime_summary


def _run_doctor() -> int:
    summary = build_runtime_summary()
    print(format_runtime_summary(summary))
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return handler()
