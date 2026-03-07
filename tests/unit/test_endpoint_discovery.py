from pathlib import Path

from llm_local.core.endpoint_discovery import (
    EndpointInfo,
    read_endpoint,
    resolve_endpoint_dir,
    write_endpoint,
)


def test_write_and_read_endpoint_round_trip(tmp_path: Path) -> None:
    endpoint_dir = tmp_path / "shared" / "vllm"
    expected = EndpointInfo(
        base_url="http://node.example.org:8000",
        health_url="http://node.example.org:8000/health",
        model="meta-llama/Llama-3-8B-Instruct",
        node="node.example.org",
        port=8000,
        slurm_job_id="12345",
        started_at="2026-03-06T12:00:00Z",
        api_key_required=True,
    )

    endpoint_path = write_endpoint(expected, endpoint_dir)
    loaded = read_endpoint(endpoint_dir)

    assert endpoint_path == endpoint_dir / "vllm-endpoint.json"
    assert loaded == expected


def test_read_endpoint_returns_none_when_missing_file(tmp_path: Path) -> None:
    assert read_endpoint(tmp_path / "missing-endpoint") is None


def test_resolve_endpoint_dir_prefers_env_var(tmp_path: Path) -> None:
    endpoint_dir = tmp_path / "group" / "vllm-endpoints"

    resolved = resolve_endpoint_dir({"VLLM_ENDPOINT_DIR": str(endpoint_dir)})

    assert resolved == endpoint_dir
    assert resolve_endpoint_dir({"VLLM_ENDPOINT_DIR": ""}) is None
    assert resolve_endpoint_dir({}) is None
