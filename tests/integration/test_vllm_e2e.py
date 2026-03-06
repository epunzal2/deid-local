from __future__ import annotations

import importlib.util
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

VLLM_TEST_MODEL_DIR = Path("models/llm/opt-125m")
VLLM_TEST_CHAT_TEMPLATE = Path("tests/fixtures/vllm_chat_template.jinja")


@pytest.mark.slow
def test_vllm_end_to_end_on_macos_cpu(tmp_path: Path) -> None:
    if sys.platform != "darwin":
        pytest.skip("macOS-only vLLM end-to-end verification test")
    if os.environ.get("DEID_RUN_VLLM_E2E") != "1":
        pytest.skip("Set DEID_RUN_VLLM_E2E=1 to run the real vLLM verification test")
    if importlib.util.find_spec("vllm") is None:
        pytest.skip("vllm is not installed in the active environment")

    repo_root = Path(__file__).resolve().parents[2]
    model_dir = repo_root / VLLM_TEST_MODEL_DIR
    chat_template_path = repo_root / VLLM_TEST_CHAT_TEMPLATE
    if not (model_dir / "config.json").is_file():
        pytest.skip(
            "Expected a local Hugging Face model snapshot at ./models/llm/opt-125m "
            "for the vLLM E2E test"
        )
    if not chat_template_path.is_file():
        pytest.skip("Expected the test chat template fixture to exist")

    vllm_bin = shutil.which("vllm")
    if vllm_bin is None:
        pytest.skip("The active environment does not provide the `vllm` CLI")

    port = _reserve_port()
    base_url = f"http://127.0.0.1:{port}"
    health_url = f"{base_url}/health"
    server_log = tmp_path / "vllm_server.log"
    command = [
        vllm_bin,
        "serve",
        str(model_dir),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--dtype",
        "float16",
        "--max-model-len",
        "512",
        "--chat-template",
        str(chat_template_path),
        "--chat-template-content-format",
        "string",
        "--served-model-name",
        "deid-local-vllm-test",
    ]

    with server_log.open("w", encoding="utf-8") as log_handle:
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            _wait_for_server(health_url, process, server_log)
            _assert_cli_success(
                [
                    sys.executable,
                    "-m",
                    "deid_local",
                    "llm",
                    "health",
                    "--provider",
                    "vllm",
                    "--base-url",
                    base_url,
                    "--health-url",
                    health_url,
                    "--model",
                    "deid-local-vllm-test",
                    "--wait-seconds",
                    "5",
                    "--interval-seconds",
                    "0.5",
                ],
                repo_root,
                server_log,
            )
            infer_stdout = _assert_cli_success(
                [
                    sys.executable,
                    "-m",
                    "deid_local",
                    "llm",
                    "infer",
                    "--provider",
                    "vllm",
                    "--base-url",
                    base_url,
                    "--health-url",
                    health_url,
                    "--model",
                    "deid-local-vllm-test",
                    "--max-tokens",
                    "16",
                    "--temperature",
                    "0",
                    "--prompt",
                    "Reply with exactly the word pong.",
                ],
                repo_root,
                server_log,
            )
            assert "pong" in infer_stdout.lower()
        finally:
            _stop_process(process)


def _reserve_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(health_url: str, process: subprocess.Popen[str], log_path: Path) -> None:
    deadline = time.monotonic() + 120.0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(
                "vLLM server exited before becoming healthy.\n\n"
                f"Server log:\n{log_path.read_text(encoding='utf-8', errors='ignore')}"
            )
        try:
            response = requests.get(health_url, timeout=2)
        except requests.RequestException:
            time.sleep(1)
            continue
        if response.status_code < 400:
            return
        time.sleep(1)
    raise AssertionError(
        "Timed out waiting for the local vLLM server to become healthy.\n\n"
        f"Server log:\n{log_path.read_text(encoding='utf-8', errors='ignore')}"
    )


def _assert_cli_success(command: list[str], cwd: Path, log_path: Path) -> str:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd / "src")
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(command)}\n\n"
            f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\n"
            f"Server log:\n{log_path.read_text(encoding='utf-8', errors='ignore')}"
        )
    return result.stdout


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)
