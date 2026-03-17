"""Shared filesystem endpoint discovery helpers for HPC vLLM serving."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

_ENDPOINT_FILENAME = "vllm-endpoint.json"


@dataclass(frozen=True, slots=True)
class EndpointInfo:
    """Public endpoint details published by a running vLLM SLURM job."""

    base_url: str
    health_url: str
    model: str
    node: str
    port: int
    slurm_job_id: str
    started_at: str
    api_key_required: bool


def read_endpoint(endpoint_dir: str | Path) -> EndpointInfo | None:
    """Read endpoint metadata from a shared endpoint directory."""

    endpoint_path = _endpoint_file_path(endpoint_dir)
    if not endpoint_path.exists():
        return None

    payload = json.loads(endpoint_path.read_text(encoding="utf-8"))
    return EndpointInfo(
        base_url=str(payload["base_url"]),
        health_url=str(payload["health_url"]),
        model=str(payload["model"]),
        node=str(payload["node"]),
        port=int(payload["port"]),
        slurm_job_id=str(payload.get("slurm_job_id", "")),
        started_at=str(payload.get("started_at", "")),
        api_key_required=_coerce_bool(payload.get("api_key_required", False)),
    )


def write_endpoint(info: EndpointInfo, endpoint_dir: str | Path) -> Path:
    """Write endpoint metadata to the shared endpoint JSON file."""

    endpoint_path = _endpoint_file_path(endpoint_dir)
    endpoint_path.parent.mkdir(parents=True, exist_ok=True)
    endpoint_path.write_text(
        json.dumps(asdict(info), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return endpoint_path


def resolve_endpoint_dir(environ: Mapping[str, str] | None = None) -> Path | None:
    """Resolve shared endpoint directory from `VLLM_ENDPOINT_DIR` when configured."""

    env = environ if environ is not None else os.environ
    raw_value = env.get("VLLM_ENDPOINT_DIR")
    if raw_value is None or raw_value == "":
        return None
    return Path(raw_value).expanduser()


def _endpoint_file_path(endpoint_dir: str | Path) -> Path:
    return Path(endpoint_dir) / _ENDPOINT_FILENAME


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes"}:
            return True
        if normalized in {"0", "false", "no"}:
            return False
    if isinstance(value, int):
        return bool(value)
    raise ValueError(f"Invalid boolean value: {value!r}")
