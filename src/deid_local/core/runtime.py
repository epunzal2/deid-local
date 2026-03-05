"""Runtime helpers for local and HPC execution contexts."""

from __future__ import annotations

import os
import platform
import sys
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeSummary:
    """Small, testable summary of the current execution environment."""

    platform_name: str
    python_version: str
    execution_target: str
    cuda_visible_devices: str | None
    slurm_job_id: str | None


def build_runtime_summary(
    environ: Mapping[str, str] | None = None,
    *,
    platform_name: str | None = None,
    python_version: str | None = None,
) -> RuntimeSummary:
    env = environ if environ is not None else os.environ
    resolved_platform = platform_name or platform.system()
    resolved_python = python_version or ".".join(str(part) for part in sys.version_info[:3])

    execution_target = "local-dev"
    if resolved_platform == "Darwin":
        execution_target = "macos-local"
    elif resolved_platform == "Linux" and (
        env.get("SLURM_JOB_ID") or env.get("CUDA_VISIBLE_DEVICES")
    ):
        execution_target = "linux-hpc-gpu"

    return RuntimeSummary(
        platform_name=resolved_platform,
        python_version=resolved_python,
        execution_target=execution_target,
        cuda_visible_devices=env.get("CUDA_VISIBLE_DEVICES"),
        slurm_job_id=env.get("SLURM_JOB_ID"),
    )


def format_runtime_summary(summary: RuntimeSummary) -> str:
    lines = [
        "deid-local doctor",
        f"Platform: {summary.platform_name}",
        f"Python: {summary.python_version}",
        f"Execution target: {summary.execution_target}",
        f"CUDA_VISIBLE_DEVICES: {summary.cuda_visible_devices or 'unset'}",
        f"SLURM_JOB_ID: {summary.slurm_job_id or 'unset'}",
    ]
    return "\n".join(lines)
