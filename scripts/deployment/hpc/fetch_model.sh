#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: fetch_model.sh --repo-id <repo> --output-dir <path> [options]

Download a Hugging Face model snapshot for HPC vLLM serving.

Options:
  --repo-id <repo>         Hugging Face repository ID (required)
  --output-dir <path>      Destination directory on shared storage (required)
  --token <token>          Hugging Face token (default: HF_TOKEN env var)
  --revision <ref>         Optional branch/tag/commit revision
  --help                   Show this help message
USAGE
}

REPO_ID=""
OUTPUT_DIR=""
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

if [[ -z "${REPO_ID}" ]]; then
    echo "Error: --repo-id is required." >&2
    usage >&2
    exit 1
fi

if [[ -z "${OUTPUT_DIR}" ]]; then
    echo "Error: --output-dir is required." >&2
    usage >&2
    exit 1
fi

CMD=(
    uv run llm-local model fetch-hf
    --repo-id "${REPO_ID}"
    --output-dir "${OUTPUT_DIR}"
)
if [[ -n "${TOKEN}" ]]; then
    CMD+=(--token "${TOKEN}")
fi
if [[ -n "${REVISION}" ]]; then
    CMD+=(--revision "${REVISION}")
fi

echo "Downloading snapshot:"
echo "  repo: ${REPO_ID}"
echo "  output: ${OUTPUT_DIR}"
if [[ -n "${REVISION}" ]]; then
    echo "  revision: ${REVISION}"
fi

"${CMD[@]}"
