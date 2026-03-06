from pathlib import Path

from llm_local.cli import build_parser, main
from llm_local.core.endpoint_discovery import EndpointInfo, write_endpoint


def test_doctor_command_prints_runtime_summary(capsys) -> None:
    exit_code = main(["doctor"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "llm-local doctor" in captured.out
    assert "Execution target:" in captured.out


def test_main_without_subcommand_prints_help(capsys) -> None:
    exit_code = main([])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Utilities for developing local-first LLM workflows" in captured.out


def test_llm_config_redacts_api_key(monkeypatch, capsys) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai_http")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-token")

    exit_code = main(["llm", "config"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "<redacted>" in captured.out
    assert "secret-token" not in captured.out


def test_model_verify_reports_missing_path(capsys, tmp_path: Path) -> None:
    missing_model = tmp_path / "missing.gguf"

    exit_code = main(["model", "verify", "--path", str(missing_model)])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "not found" in captured.err


def test_model_fetch_hf_parser_accepts_expected_options() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "model",
            "fetch-hf",
            "--repo-id",
            "meta-llama/Llama-3-8B-Instruct",
            "--output-dir",
            "/shared/models/Llama-3-8B-Instruct",
            "--revision",
            "main",
        ]
    )

    assert args.command == "model"
    assert args.model_command == "fetch-hf"
    assert args.repo_id == "meta-llama/Llama-3-8B-Instruct"
    assert args.output_dir == "/shared/models/Llama-3-8B-Instruct"
    assert args.revision == "main"


def test_model_fetch_hf_uses_hf_token_from_env(monkeypatch, capsys, tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshot"
    calls: dict[str, object] = {}

    def _fake_download_hf_snapshot(  # type: ignore[no-untyped-def]
        repo_id,
        output_dir,
        *,
        token,
        revision,
    ):
        calls["repo_id"] = repo_id
        calls["output_dir"] = output_dir
        calls["token"] = token
        calls["revision"] = revision
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        return snapshot_dir

    monkeypatch.setenv("HF_TOKEN", "token-from-env")
    monkeypatch.setattr("llm_local.cli.download_hf_snapshot", _fake_download_hf_snapshot)

    exit_code = main(
        [
            "model",
            "fetch-hf",
            "--repo-id",
            "meta-llama/Llama-3-8B-Instruct",
            "--output-dir",
            str(tmp_path / "models"),
            "--revision",
            "main",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert str(snapshot_dir) in captured.out
    assert calls == {
        "repo_id": "meta-llama/Llama-3-8B-Instruct",
        "output_dir": str(tmp_path / "models"),
        "token": "token-from-env",
        "revision": "main",
    }


def test_llm_connect_prints_exports_from_endpoint_file(capsys, tmp_path: Path) -> None:
    endpoint_dir = tmp_path / "shared" / "endpoints"
    write_endpoint(
        EndpointInfo(
            base_url="http://node01.example.edu:8000",
            health_url="http://node01.example.edu:8000/health",
            model="meta-llama/Llama-3-8B-Instruct",
            node="node01.example.edu",
            port=8000,
            slurm_job_id="98765",
            started_at="2026-03-06T15:00:00Z",
            api_key_required=True,
        ),
        endpoint_dir,
    )

    exit_code = main(
        [
            "llm",
            "connect",
            "--endpoint-dir",
            str(endpoint_dir),
            "--api-key",
            "shared-token",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "export LLM_PROVIDER=vllm" in captured.out
    assert f"export VLLM_ENDPOINT_DIR={endpoint_dir}" in captured.out
    assert "export VLLM_BASE_URL=http://node01.example.edu:8000" in captured.out
    assert "export VLLM_HEALTH_URL=http://node01.example.edu:8000/health" in captured.out
    assert "export VLLM_MODEL=meta-llama/Llama-3-8B-Instruct" in captured.out
    assert "export VLLM_API_KEY=shared-token" in captured.out
