#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
HOST="${CHAT_HOST:-127.0.0.1}"
PORT="${CHAT_PORT:-8088}"

cd "${PROJECT_ROOT}"

uv run llm-local llm chat --host "${HOST}" --port "${PORT}" "$@"
