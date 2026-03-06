#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: download_vllm_model.sh [options]

Download-only helper for vLLM model snapshots. Intended for login/data-transfer
nodes where long downloads are more reliable than compute nodes.

Options:
  --repo-id <repo>         Hugging Face repository ID
                           (default: env VLLM_MODEL_REPO or
                           meta-llama/Llama-3-8B-Instruct)
  --output-dir <path>      Destination directory on shared storage
                           (default: env SHARED_MODEL_DIR)
  --token <token>          Hugging Face token (default: HF_TOKEN env var)
  --revision <ref>         Optional branch/tag/commit revision
  --help                   Show this help message
USAGE
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
FETCH_SCRIPT="${SCRIPT_DIR}/fetch_model.sh"

REPO_ID="${VLLM_MODEL_REPO:-meta-llama/Llama-3-8B-Instruct}"
OUTPUT_DIR="${SHARED_MODEL_DIR:-}"
TOKEN="${HF_TOKEN:-}"
REVISION=""

while (($# > 0)); do
    case "$1" in
        --repo-id)
            REPO_ID="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --token)
            TOKEN="$2"
            shift 2
            ;;
        --revision)
            REVISION="$2"
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

if [[ -z "${OUTPUT_DIR}" ]]; then
    echo "Error: --output-dir is required (or set SHARED_MODEL_DIR)." >&2
    usage >&2
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

echo "Download-only step (recommended on login/data-transfer node)."
echo "Starting model snapshot download..."

CMD=("${FETCH_SCRIPT}" --repo-id "${REPO_ID}" --output-dir "${OUTPUT_DIR}")
if [[ -n "${TOKEN}" ]]; then
    CMD+=(--token "${TOKEN}")
fi
if [[ -n "${REVISION}" ]]; then
    CMD+=(--revision "${REVISION}")
fi

"${CMD[@]}"
