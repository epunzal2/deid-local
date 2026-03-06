from pathlib import Path

import pytest

HPC_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts" / "deployment" / "hpc"
VLLM_SERVE_SCRIPT = HPC_SCRIPT_DIR / "vllm_serve.sbatch"
SUBMIT_VLLM_SERVE_SCRIPT = HPC_SCRIPT_DIR / "submit_vllm_serve.sh"


def _sbatch_files() -> list[Path]:
    files = sorted(HPC_SCRIPT_DIR.glob("*.sbatch"))
    assert files, f"No .sbatch files found under {HPC_SCRIPT_DIR}"
    return files


def test_sbatch_files_start_with_shebang_and_include_sbatch_directives() -> None:
    for script_path in _sbatch_files():
        content = script_path.read_text(encoding="utf-8")
        assert content.startswith("#!/usr/bin/env bash"), f"Missing bash shebang in {script_path}"
        assert "#SBATCH" in content, f"Missing #SBATCH directives in {script_path}"


def test_vllm_serve_sbatch_has_required_hpc_directives() -> None:
    content = VLLM_SERVE_SCRIPT.read_text(encoding="utf-8")

    required_directives = [
        "#SBATCH --partition=gpu-redhat",
        "#SBATCH --constraint='volta|adalovelace|ampere'",
        "#SBATCH --output=logs/%x_%N_%j.out",
        "#SBATCH --error=logs/%x_%N_%j.err",
    ]
    for directive in required_directives:
        assert directive in content, f"Missing required directive: {directive}"


def test_submit_vllm_serve_defaults_to_gpu_redhat_partition() -> None:
    content = SUBMIT_VLLM_SERVE_SCRIPT.read_text(encoding="utf-8")
    assert 'PARTITION="${SLURM_PARTITION:-gpu-redhat}"' in content
    assert "--partition)" in content


@pytest.mark.parametrize(
    "forbidden_pattern",
    [
        "/Users/",
        "/home/",
        "/gpfs/home/",
        "/nfs/home/",
        "exequielpunzalan",
    ],
)
def test_sbatch_files_do_not_hardcode_user_paths(forbidden_pattern: str) -> None:
    for script_path in _sbatch_files():
        content = script_path.read_text(encoding="utf-8")
        assert forbidden_pattern not in content, (
            f"Forbidden hard-coded path pattern {forbidden_pattern!r} in {script_path}"
        )
