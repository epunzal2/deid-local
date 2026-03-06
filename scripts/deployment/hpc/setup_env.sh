#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"

cd "${PROJECT_ROOT}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it or load it in your HPC environment." >&2
  exit 1
fi

uv sync --extra dev

cat <<'EOF'
Base HPC environment is ready.

Optional follow-up commands:
  uv sync --extra dev --extra llama_cpp
  uv run llm-local llm health --provider vllm
  sbatch scripts/deployment/hpc/vllm_smoke.sbatch
EOF
