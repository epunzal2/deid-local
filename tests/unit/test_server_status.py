from __future__ import annotations

import subprocess
from typing import Any

import requests

from llm_local.core.endpoint_discovery import EndpointInfo
from llm_local.core.server_status import build_server_status, format_server_status


class _FakeResponse:
    def __init__(self, status_code: int, payload: Any | None = None) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class _FakeSession:
    def __init__(self, responses: dict[str, _FakeResponse | Exception]) -> None:
        self._responses = responses
        self.calls: list[tuple[str, dict[str, str], float]] = []

    def get(self, url: str, *, headers: dict[str, str], timeout: float) -> _FakeResponse:
        self.calls.append((url, headers, timeout))
        response = self._responses[url]
        if isinstance(response, Exception):
            raise response
        return response


def test_build_server_status_reports_healthy_with_model_and_slurm_state() -> None:
    endpoint = EndpointInfo(
        base_url="http://node01.example.edu:8000",
        health_url="http://node01.example.edu:8000/health",
        model="meta-llama/Llama-3-8B-Instruct",
        node="node01.example.edu",
        port=8000,
        slurm_job_id="43210",
        started_at="2026-03-06T18:00:00Z",
        api_key_required=True,
    )
    session = _FakeSession(
        {
            endpoint.health_url: _FakeResponse(200, {"status": "ok"}),
            f"{endpoint.base_url}/v1/models": _FakeResponse(
                200,
                {"data": [{"id": "meta-llama/Llama-3-8B-Instruct"}]},
            ),
        }
    )

    def _fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["squeue"],
            returncode=0,
            stdout="RUNNING\n",
            stderr="",
        )

    status = build_server_status(
        endpoint,
        api_key="shared-token",
        session=session,
        run_command=_fake_run,
    )

    assert status.healthy is True
    assert status.http_status_code == 200
    assert status.slurm_state == "RUNNING"
    assert status.model_info == {"data": [{"id": "meta-llama/Llama-3-8B-Instruct"}]}
    assert status.error is None
    assert session.calls[0][1]["Authorization"] == "Bearer shared-token"

    rendered = format_server_status(status)
    assert "Health: healthy" in rendered
    assert "SLURM state: RUNNING" in rendered
    assert "Served models: meta-llama/Llama-3-8B-Instruct" in rendered


def test_build_server_status_handles_unhealthy_and_missing_squeue() -> None:
    endpoint = EndpointInfo(
        base_url="http://node02.example.edu:8000",
        health_url="http://node02.example.edu:8000/health",
        model="meta-llama/Llama-3-8B-Instruct",
        node="node02.example.edu",
        port=8000,
        slurm_job_id="99999",
        started_at="2026-03-06T18:05:00Z",
        api_key_required=False,
    )
    session = _FakeSession(
        {
            endpoint.health_url: _FakeResponse(503, {"status": "starting"}),
            f"{endpoint.base_url}/v1/models": requests.ConnectionError("connection failed"),
        }
    )

    def _missing_squeue(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("squeue not found")

    status = build_server_status(
        endpoint,
        api_key=None,
        session=session,
        run_command=_missing_squeue,
    )

    assert status.healthy is False
    assert status.http_status_code == 503
    assert status.slurm_state == "squeue-unavailable"
    assert status.model_info is None
    assert status.error is not None
    assert "HTTP 503" in status.error

    rendered = format_server_status(status)
    assert "Health: unhealthy" in rendered
    assert "SLURM state: squeue-unavailable" in rendered
    assert "Error:" in rendered
