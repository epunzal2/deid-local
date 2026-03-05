#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
HOST="${DEID_CHAT_HOST:-127.0.0.1}"
PORT="${DEID_CHAT_PORT:-8088}"

cd "${PROJECT_ROOT}"

uv run deid-local llm chat --host "${HOST}" --port "${PORT}" "$@"
