#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"

cd "${PROJECT_ROOT}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it before running this script." >&2
  exit 1
fi

uv sync --managed-python --python 3.12.9 --extra dev --extra llama_cpp --extra models

cat <<'EOF'
Local llama.cpp environment is ready.

Suggested next steps:
  uv run deid-local model fetch
  uv run deid-local llm health --provider llama_cpp
  uv run deid-local llm infer --provider llama_cpp --prompt "Reply with pong."
  scripts/deployment/macos/run_chat_window.sh
EOF
