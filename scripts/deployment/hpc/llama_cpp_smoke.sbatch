#!/usr/bin/env bash
#SBATCH --job-name=deid-llama-smoke
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --time=00:15:00
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-$PWD}}"
MODEL_PATH="${LLAMA_MODEL_PATH:-./models/llm/Phi-3-mini-4k-instruct-q4.gguf}"
PROMPT="${SMOKE_PROMPT:-Reply with pong.}"

cd "${PROJECT_ROOT}"
mkdir -p logs

export PYTHONUNBUFFERED=1

echo "Project root: ${PROJECT_ROOT}"
echo "Node: $(hostname -f)"
echo "Model path: ${MODEL_PATH}"

uv run llm-local llm health --provider llama_cpp --model-path "${MODEL_PATH}"
uv run llm-local llm infer --provider llama_cpp --model-path "${MODEL_PATH}" --prompt "${PROMPT}"
