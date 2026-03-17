#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: verify_vllm_serve.sh [options]

Run targeted vLLM serve validation tests and save a timestamped log under
./verification.

Options:
  --help  Show this help message
USAGE
}

while (($# > 0)); do
  case "$1" in
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown option '$1'." >&2
      usage >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
ARTIFACT_DIR="${PROJECT_ROOT}/verification"
LOG_PATH="${ARTIFACT_DIR}/vllm_serve_verify_${TIMESTAMP}.log"

mkdir -p "${ARTIFACT_DIR}"

export PYTHONPATH="${PROJECT_ROOT}/src"
export RUN_VLLM_E2E="${RUN_VLLM_E2E:-0}"
export RUN_LLAMA_CPP_E2E="${RUN_LLAMA_CPP_E2E:-0}"

if command -v uv >/dev/null 2>&1; then
  TEST_CMD=(
    uv run pytest
    tests/unit/test_slurm_scripts.py
    tests/unit/test_endpoint_discovery.py
    tests/unit/test_server_status.py
    tests/integration/test_http_cli.py
    tests/integration/test_concurrent_requests.py
    -vv -s
  )
else
  TEST_CMD=(
    python -m pytest
    tests/unit/test_slurm_scripts.py
    tests/unit/test_endpoint_discovery.py
    tests/unit/test_server_status.py
    tests/integration/test_http_cli.py
    tests/integration/test_concurrent_requests.py
    -vv -s
  )
fi

{
  echo "UTC timestamp: ${TIMESTAMP}"
  echo "Project root: ${PROJECT_ROOT}"
  echo "Python: $(python -V 2>&1)"
  echo "RUN_VLLM_E2E: ${RUN_VLLM_E2E}"
  echo "RUN_LLAMA_CPP_E2E: ${RUN_LLAMA_CPP_E2E}"
  echo "Command: ${TEST_CMD[*]}"
  "${TEST_CMD[@]}"
} | tee "${LOG_PATH}"

echo "Verification log saved to ${LOG_PATH}"
