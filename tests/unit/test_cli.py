from deid_local.cli import main


def test_doctor_command_prints_runtime_summary(capsys) -> None:
    exit_code = main(["doctor"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "deid-local doctor" in captured.out
    assert "Execution target:" in captured.out


def test_main_without_subcommand_prints_help(capsys) -> None:
    exit_code = main([])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Utilities for developing local-first LLM workflows" in captured.out
