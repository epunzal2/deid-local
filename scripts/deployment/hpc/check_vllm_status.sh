#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: check_vllm_status.sh [options]

Check status of the shared vLLM serve endpoint.

Options:
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

ENDPOINT_DIR="${VLLM_ENDPOINT_DIR:-}"

while (($# > 0)); do
    case "$1" in
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

if [[ -z "${ENDPOINT_DIR}" ]]; then
    echo "Error: endpoint directory is required via --endpoint-dir or VLLM_ENDPOINT_DIR." >&2
    exit 1
fi

ENDPOINT_FILE="${ENDPOINT_DIR}/vllm-endpoint.json"
if [[ ! -f "${ENDPOINT_FILE}" ]]; then
    echo "Error: endpoint file not found: ${ENDPOINT_FILE}" >&2
    exit 1
fi

PYTHON_BIN="$(resolve_python_bin)"

read -r BASE_URL HEALTH_URL MODEL NODE PORT SLURM_JOB_ID STARTED_AT API_KEY_REQUIRED < <(
    "${PYTHON_BIN}" - "${ENDPOINT_FILE}" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)

def normalize(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)

fields = [
    normalize(payload.get("base_url")),
    normalize(payload.get("health_url")),
    normalize(payload.get("model")),
    normalize(payload.get("node")),
    normalize(payload.get("port")),
    normalize(payload.get("slurm_job_id")),
    normalize(payload.get("started_at")),
    normalize(payload.get("api_key_required")),
]
print("\t".join(fields))
PY
)

if [[ -z "${HEALTH_URL}" ]]; then
    echo "Error: endpoint file is missing 'health_url'." >&2
    exit 1
fi

SLURM_STATE="missing-job-id"
if [[ -n "${SLURM_JOB_ID}" ]]; then
    if command -v squeue >/dev/null 2>&1; then
        SQUEUE_STATE="$(squeue -h -j "${SLURM_JOB_ID}" -o "%T" 2>/dev/null | head -n 1 || true)"
        SLURM_STATE="${SQUEUE_STATE:-not-found}"
    else
        SLURM_STATE="squeue-unavailable"
    fi
fi

HTTP_CODE="$(curl -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}" 2>/dev/null || echo "000")"
HEALTHY="false"
if [[ "${HTTP_CODE}" != "000" ]] && [[ "${HTTP_CODE}" -lt 400 ]]; then
    HEALTHY="true"
fi

echo "vLLM endpoint: ${ENDPOINT_FILE}"
echo "  base_url: ${BASE_URL}"
echo "  health_url: ${HEALTH_URL}"
echo "  model: ${MODEL}"
echo "  node: ${NODE}"
echo "  port: ${PORT}"
echo "  slurm_job_id: ${SLURM_JOB_ID:-<unset>}"
echo "  slurm_state: ${SLURM_STATE}"
echo "  started_at: ${STARTED_AT:-<unset>}"
echo "  api_key_required: ${API_KEY_REQUIRED:-false}"
echo "  health_http_code: ${HTTP_CODE}"
echo "  healthy: ${HEALTHY}"

if [[ "${HEALTHY}" == "true" ]]; then
    exit 0
fi
exit 1
