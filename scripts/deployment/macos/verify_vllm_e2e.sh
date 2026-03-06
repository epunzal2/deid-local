#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
ARTIFACT_DIR="${PROJECT_ROOT}/verification"
LOG_PATH="${ARTIFACT_DIR}/vllm_e2e_${TIMESTAMP}.log"
DEFAULT_MODEL_DIR="${PROJECT_ROOT}/models/llm/opt-125m"
DEFAULT_VENV_PATH="${PROJECT_ROOT}/.venv"
SIBLING_VENV_PATH="${PROJECT_ROOT}/../deid-local/.venv"

_venv_has_vllm() {
  local venv_path="$1"
  "${venv_path}/bin/python" - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("vllm") else 1)
PY
}

if [[ ! -f "${DEFAULT_MODEL_DIR}/config.json" ]]; then
  cat >&2 <<EOF
Expected a local Hugging Face model snapshot at:
  ${DEFAULT_MODEL_DIR}

Populate it with something small enough for a CPU smoke test, for example:
  huggingface-cli download facebook/opt-125m --local-dir ${DEFAULT_MODEL_DIR} --local-dir-use-symlinks False
EOF
  exit 1
fi

VENV_PATH="${DEID_VENV_PATH:-}"
if [[ -z "${VENV_PATH}" ]]; then
  if [[ -x "${DEFAULT_VENV_PATH}/bin/python" ]] && _venv_has_vllm "${DEFAULT_VENV_PATH}"; then
    VENV_PATH="${DEFAULT_VENV_PATH}"
  elif [[ -x "${SIBLING_VENV_PATH}/bin/python" ]] && _venv_has_vllm "${SIBLING_VENV_PATH}"; then
    VENV_PATH="${SIBLING_VENV_PATH}"
  else
    echo "No usable virtual environment with vllm found at ${DEFAULT_VENV_PATH} or ${SIBLING_VENV_PATH}" >&2
    exit 1
  fi
fi

mkdir -p "${ARTIFACT_DIR}"

source "${VENV_PATH}/bin/activate"

if ! python - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("vllm") else 1)
PY
then
  echo "Selected virtual environment does not provide vllm: ${VENV_PATH}" >&2
  exit 1
fi

export PYTHONPATH="${PROJECT_ROOT}/src"
export DEID_RUN_VLLM_E2E=1

{
  echo "UTC timestamp: ${TIMESTAMP}"
  echo "Project root: ${PROJECT_ROOT}"
  echo "Virtualenv: ${VENV_PATH}"
  echo "Model dir: ${DEFAULT_MODEL_DIR}"
  echo "Python: $(python -V 2>&1)"
  python -m pytest tests/integration/test_vllm_e2e.py -vv -s
} | tee "${LOG_PATH}"

echo "Verification log saved to ${LOG_PATH}"
