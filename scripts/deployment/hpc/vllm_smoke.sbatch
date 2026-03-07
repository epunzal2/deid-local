#!/usr/bin/env bash
#SBATCH --job-name=deid-vllm-smoke
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --time=00:10:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-$PWD}}"
BASE_URL="${VLLM_BASE_URL:-http://127.0.0.1:8000}"
HEALTH_URL="${VLLM_HEALTH_URL:-http://127.0.0.1:8000/health}"
MODEL="${VLLM_MODEL:-meta-llama/Llama-3-8B-Instruct}"
PROMPT="${SMOKE_PROMPT:-Reply with pong.}"

cd "${PROJECT_ROOT}"
mkdir -p logs

export PYTHONUNBUFFERED=1

echo "Project root: ${PROJECT_ROOT}"
echo "Node: $(hostname -f)"
echo "Base URL: ${BASE_URL}"
echo "Health URL: ${HEALTH_URL}"
echo "Model: ${MODEL}"

uv run llm-local llm health \
  --provider vllm \
  --base-url "${BASE_URL}" \
  --model "${MODEL}" \
  --health-url "${HEALTH_URL}" \
  --wait-seconds 30 \
  --interval-seconds 5

uv run llm-local llm infer \
  --provider vllm \
  --base-url "${BASE_URL}" \
  --model "${MODEL}" \
  --prompt "${PROMPT}"
