from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from llm_local.core.llm_settings import DEFAULT_TEST_MODEL_PATH


@pytest.mark.slow
def test_llama_cpp_end_to_end_on_macos() -> None:
    if sys.platform != "darwin":
        pytest.skip("macOS-only end-to-end verification test")
    if os.environ.get("RUN_LLAMA_CPP_E2E") != "1":
        pytest.skip("Set RUN_LLAMA_CPP_E2E=1 to run the real llama.cpp verification test")
    if importlib.util.find_spec("llama_cpp") is None:
        pytest.skip("llama-cpp-python is not installed in the active environment")

    repo_root = Path(__file__).resolve().parents[2]
    model_path = _resolve_model_path(repo_root)
    if model_path is None:
        pytest.skip("No local Phi-3 GGUF found in the repo or sibling main worktree")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")
    env["LLAMA_MODEL_PATH"] = str(model_path)

    health_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "llm_local",
            "llm",
            "health",
            "--provider",
            "llama_cpp",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert health_result.returncode == 0, health_result.stderr or health_result.stdout

    infer_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "llm_local",
            "llm",
            "infer",
            "--provider",
            "llama_cpp",
            "--max-tokens",
            "16",
            "--temperature",
            "0",
            "--prompt",
            "Reply with exactly the word pong.",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert infer_result.returncode == 0, infer_result.stderr or infer_result.stdout
    assert "pong" in infer_result.stdout.lower()


def _resolve_model_path(repo_root: Path) -> Path | None:
    model_path = repo_root / DEFAULT_TEST_MODEL_PATH
    return model_path if model_path.is_file() else None
