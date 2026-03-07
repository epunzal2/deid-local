#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: stop_vllm_serve.sh [options]

Stop a vLLM serve SLURM job and remove its shared endpoint file.

Options:
  --job-id <id>          SLURM job ID to cancel. If omitted, read from endpoint file.
  --endpoint-dir <path>  Directory containing vllm-endpoint.json
                         (default: VLLM_ENDPOINT_DIR env var)
  --help                 Show this help message
USAGE
}

resolve_python_bin() {
    if command -v python3 >/dev/null 2>&1; then
        echo "python3"
        return
    fi
    if command -v python >/dev/null 2>&1; then
        echo "python"
        return
    fi
    echo "Error: Python is required to parse endpoint JSON." >&2
    exit 1
}

JOB_ID=""
ENDPOINT_DIR="${VLLM_ENDPOINT_DIR:-}"

while (($# > 0)); do
    case "$1" in
        --job-id)
            JOB_ID="$2"
            shift 2
            ;;
        --endpoint-dir)
            ENDPOINT_DIR="$2"
            shift 2
            ;;
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

if [[ -z "${JOB_ID}" ]] && [[ -z "${ENDPOINT_DIR}" ]]; then
    echo "Error: provide --job-id or --endpoint-dir (or set VLLM_ENDPOINT_DIR)." >&2
    exit 1
fi

ENDPOINT_FILE=""
if [[ -n "${ENDPOINT_DIR}" ]]; then
    ENDPOINT_FILE="${ENDPOINT_DIR}/vllm-endpoint.json"
fi

if [[ -z "${JOB_ID}" ]] && [[ -n "${ENDPOINT_FILE}" ]] && [[ -f "${ENDPOINT_FILE}" ]]; then
    PYTHON_BIN="$(resolve_python_bin)"
    JOB_ID="$("${PYTHON_BIN}" - "${ENDPOINT_FILE}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

print(payload.get("slurm_job_id", ""))
PY
)"
fi

SCANCEL_FAILED="false"
if [[ -n "${JOB_ID}" ]]; then
    if command -v scancel >/dev/null 2>&1; then
        if scancel "${JOB_ID}"; then
            echo "Cancelled SLURM job: ${JOB_ID}"
        else
            echo "Warning: failed to cancel SLURM job: ${JOB_ID}" >&2
            SCANCEL_FAILED="true"
        fi
    else
        echo "Warning: scancel not found; could not cancel job ${JOB_ID}." >&2
        SCANCEL_FAILED="true"
    fi
else
    echo "No SLURM job ID found to cancel."
fi

if [[ -n "${ENDPOINT_FILE}" ]] && [[ -f "${ENDPOINT_FILE}" ]]; then
    rm -f "${ENDPOINT_FILE}"
    echo "Removed endpoint file: ${ENDPOINT_FILE}"
elif [[ -n "${ENDPOINT_FILE}" ]]; then
    echo "Endpoint file not present: ${ENDPOINT_FILE}"
fi

if [[ "${SCANCEL_FAILED}" == "true" ]]; then
    exit 1
fi
exit 0
