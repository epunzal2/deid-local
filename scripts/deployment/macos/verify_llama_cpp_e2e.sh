#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
ARTIFACT_DIR="${PROJECT_ROOT}/verification"
LOG_PATH="${ARTIFACT_DIR}/llama_cpp_e2e_${TIMESTAMP}.log"
DEFAULT_MODEL_PATH="${PROJECT_ROOT}/models/llm/Phi-3-mini-4k-instruct-q4.gguf"
DEFAULT_VENV_PATH="${PROJECT_ROOT}/.venv"
SIBLING_VENV_PATH="${PROJECT_ROOT}/../deid-local/.venv"

_venv_has_llama_cpp() {
  local venv_path="$1"
  "${venv_path}/bin/python" - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("llama_cpp") else 1)
PY
}

MODEL_PATH="${DEFAULT_MODEL_PATH}"
if [[ ! -f "${MODEL_PATH}" ]]; then
  echo "No GGUF found at ${DEFAULT_MODEL_PATH}" >&2
  exit 1
fi

VENV_PATH="${DEID_VENV_PATH:-}"
if [[ -z "${VENV_PATH}" ]]; then
  if [[ -x "${DEFAULT_VENV_PATH}/bin/python" ]] && _venv_has_llama_cpp "${DEFAULT_VENV_PATH}"; then
    VENV_PATH="${DEFAULT_VENV_PATH}"
  elif [[ -x "${SIBLING_VENV_PATH}/bin/python" ]] && _venv_has_llama_cpp "${SIBLING_VENV_PATH}"; then
    VENV_PATH="${SIBLING_VENV_PATH}"
  else
    echo "No usable virtual environment with llama_cpp found at ${DEFAULT_VENV_PATH} or ${SIBLING_VENV_PATH}" >&2
    exit 1
  fi
fi

mkdir -p "${ARTIFACT_DIR}"

source "${VENV_PATH}/bin/activate"

if ! python - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("llama_cpp") else 1)
PY
then
  echo "Selected virtual environment does not provide llama_cpp: ${VENV_PATH}" >&2
  exit 1
fi

export PYTHONPATH="${PROJECT_ROOT}/src"
export DEID_RUN_LLAMA_CPP_E2E=1

{
  echo "UTC timestamp: ${TIMESTAMP}"
  echo "Project root: ${PROJECT_ROOT}"
  echo "Virtualenv: ${VENV_PATH}"
  echo "Model path: ${MODEL_PATH}"
  echo "Python: $(python -V 2>&1)"
  python -m pytest tests/integration/test_llama_cpp_e2e.py -vv -s
} | tee "${LOG_PATH}"

echo "Verification log saved to ${LOG_PATH}"
