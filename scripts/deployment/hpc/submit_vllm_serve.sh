#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: submit_vllm_serve.sh [options]

Submit a vLLM serving SLURM job.

Options:
  --model <model-id-or-path>  Model to serve (default: env VLLM_MODEL or
                               meta-llama/Llama-3-8B-Instruct)
  --gpus <count>              GPU count and tensor parallel size (default: env
                               VLLM_TENSOR_PARALLEL or 1)
  --partition <name>          SLURM partition (default: env SLURM_PARTITION or
                               gpu-redhat)
  --time <HH:MM:SS>           SLURM walltime override
  --port <port>               Service port (default: env VLLM_PORT or 8000)
  --api-key <key>             API key passed to vLLM
  --endpoint-dir <path>       Shared directory for vllm-endpoint.json
                               (default: env VLLM_ENDPOINT_DIR)
  --max-model-len <tokens>    Max model length (default: env VLLM_MAX_MODEL_LEN
                               or 4096)
  --help                      Show this help message
USAGE
}

require_positive_integer() {
    local value="$1"
    local name="$2"
    if ! [[ "${value}" =~ ^[1-9][0-9]*$ ]]; then
        echo "Error: ${name} must be a positive integer, got '${value}'." >&2
        exit 1
    fi
}

require_port() {
    local value="$1"
    if ! [[ "${value}" =~ ^[0-9]+$ ]] || ((value < 1 || value > 65535)); then
        echo "Error: port must be an integer in [1, 65535], got '${value}'." >&2
        exit 1
    fi
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SBATCH_SCRIPT="${SCRIPT_DIR}/vllm_serve.sbatch"

MODEL="${VLLM_MODEL:-meta-llama/Llama-3-8B-Instruct}"
GPUS="${VLLM_TENSOR_PARALLEL:-1}"
PARTITION="${SLURM_PARTITION:-gpu-redhat}"
TIME_OVERRIDE=""
PORT="${VLLM_PORT:-8000}"
API_KEY="${VLLM_API_KEY:-}"
ENDPOINT_DIR="${VLLM_ENDPOINT_DIR:-}"
MAX_MODEL_LEN="${VLLM_MAX_MODEL_LEN:-4096}"

while (($# > 0)); do
    case "$1" in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --gpus)
            GPUS="$2"
            shift 2
            ;;
        --partition)
            PARTITION="$2"
            shift 2
            ;;
        --time)
            TIME_OVERRIDE="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --api-key)
            API_KEY="$2"
            shift 2
            ;;
        --endpoint-dir)
            ENDPOINT_DIR="$2"
            shift 2
            ;;
        --max-model-len)
            MAX_MODEL_LEN="$2"
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

if [[ -z "${MODEL}" ]]; then
    echo "Error: model must not be empty." >&2
    exit 1
fi

require_positive_integer "${GPUS}" "--gpus"
require_port "${PORT}"
require_positive_integer "${MAX_MODEL_LEN}" "--max-model-len"

SBATCH_ARGS=(--gres "gpu:${GPUS}")
if [[ -n "${PARTITION}" ]]; then
    SBATCH_ARGS+=(--partition "${PARTITION}")
fi
if [[ -n "${TIME_OVERRIDE}" ]]; then
    SBATCH_ARGS+=(--time "${TIME_OVERRIDE}")
fi

export VLLM_MODEL="${MODEL}"
export VLLM_TENSOR_PARALLEL="${GPUS}"
export VLLM_PORT="${PORT}"
export VLLM_MAX_MODEL_LEN="${MAX_MODEL_LEN}"

if [[ -n "${API_KEY}" ]]; then
    export VLLM_API_KEY="${API_KEY}"
fi
if [[ -n "${ENDPOINT_DIR}" ]]; then
    export VLLM_ENDPOINT_DIR="${ENDPOINT_DIR}"
fi

echo "Submitting vLLM serve job:"
echo "  script: ${SBATCH_SCRIPT}"
echo "  model: ${VLLM_MODEL}"
echo "  gpus/tensor-parallel: ${VLLM_TENSOR_PARALLEL}"
echo "  partition: ${PARTITION}"
echo "  port: ${VLLM_PORT}"
echo "  max model len: ${VLLM_MAX_MODEL_LEN}"
if [[ -n "${ENDPOINT_DIR}" ]]; then
    echo "  endpoint dir: ${ENDPOINT_DIR}"
fi
if [[ -n "${TIME_OVERRIDE}" ]]; then
    echo "  walltime: ${TIME_OVERRIDE}"
fi

submit_output="$(sbatch "${SBATCH_ARGS[@]}" "${SBATCH_SCRIPT}")"
echo "${submit_output}"

job_id="$(awk '/Submitted batch job/{print $4}' <<<"${submit_output}")"
if [[ -n "${job_id}" ]]; then
    echo "Track status with: squeue -j ${job_id}"
fi
