"""Helpers for aggregating vLLM endpoint, HTTP health, and SLURM status."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import requests

from llm_local.core.endpoint_discovery import EndpointInfo


@dataclass(frozen=True, slots=True)
class ServerStatus:
    """Aggregated service status for a shared vLLM endpoint."""

    endpoint: EndpointInfo
    healthy: bool
    http_status_code: int | None
    slurm_state: str | None
    model_info: dict[str, Any] | None
    error: str | None


def build_server_status(
    endpoint: EndpointInfo,
    api_key: str | None,
    *,
    session: requests.Session | object | None = None,
    run_command: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    timeout_seconds: float = 10.0,
) -> ServerStatus:
    """Probe HTTP health, model listing, and SLURM state for an endpoint."""

    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    requester = session or requests.Session()
    healthy = False
    http_status_code: int | None = None
    model_info: dict[str, Any] | None = None
    error: str | None = None

    try:
        health_response = requester.get(
            endpoint.health_url,
            headers=headers,
            timeout=timeout_seconds,
        )
        http_status_code = health_response.status_code
        healthy = health_response.status_code < 400
        if not healthy:
            error = (
                f"Health probe returned HTTP {health_response.status_code} for "
                f"{endpoint.health_url}"
            )
    except requests.RequestException as exc:
        error = f"Health probe failed for {endpoint.health_url}: {exc}"

    models_url = f"{endpoint.base_url.rstrip('/')}/v1/models"
    try:
        models_response = requester.get(
            models_url,
            headers=headers,
            timeout=timeout_seconds,
        )
        if models_response.status_code < 400:
            payload = models_response.json()
            if isinstance(payload, dict):
                model_info = payload
            elif error is None:
                payload_type = type(payload).__name__
                error = f"Unexpected models payload type from {models_url}: {payload_type}"
        elif error is None:
            error = f"Model listing returned HTTP {models_response.status_code} for {models_url}"
    except (requests.RequestException, ValueError) as exc:
        if error is None:
            error = f"Model listing failed for {models_url}: {exc}"

    slurm_state = _read_slurm_state(endpoint.slurm_job_id, run_command=run_command)
    return ServerStatus(
        endpoint=endpoint,
        healthy=healthy,
        http_status_code=http_status_code,
        slurm_state=slurm_state,
        model_info=model_info,
        error=error,
    )


def format_server_status(status: ServerStatus) -> str:
    """Render a human-friendly summary of aggregated endpoint status."""

    model_ids = _extract_model_ids(status.model_info)
    lines = [
        "llm-local status",
        f"Endpoint: {status.endpoint.base_url}",
        f"Health URL: {status.endpoint.health_url}",
        f"Model: {status.endpoint.model}",
        f"Node: {status.endpoint.node}",
        f"Port: {status.endpoint.port}",
        f"SLURM job: {status.endpoint.slurm_job_id or 'unset'}",
        f"SLURM state: {status.slurm_state or 'unknown'}",
        f"Health: {'healthy' if status.healthy else 'unhealthy'}",
        "HTTP status: "
        f"{status.http_status_code if status.http_status_code is not None else 'none'}",
        f"Served models: {', '.join(model_ids) if model_ids else 'unknown'}",
    ]
    if status.error:
        lines.append(f"Error: {status.error}")
    return "\n".join(lines)


def _read_slurm_state(
    slurm_job_id: str,
    *,
    run_command: Callable[..., subprocess.CompletedProcess[str]],
) -> str:
    if not slurm_job_id:
        return "missing-job-id"
    try:
        result = run_command(
            ["squeue", "-h", "-j", slurm_job_id, "-o", "%T"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return "squeue-unavailable"
    except OSError:
        return "squeue-error"

    if result.returncode != 0:
        return "squeue-error"
    state = result.stdout.strip().splitlines()
    if not state:
        return "not-found"
    return state[0]


def _extract_model_ids(model_info: dict[str, Any] | None) -> list[str]:
    if model_info is None:
        return []
    data = model_info.get("data")
    if not isinstance(data, list):
        return []
    model_ids: list[str] = []
    for item in data:
        if isinstance(item, dict):
            model_id = item.get("id")
            if isinstance(model_id, str) and model_id:
                model_ids.append(model_id)
    return model_ids
