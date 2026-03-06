from pathlib import Path

from llm_local.cli import main


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
