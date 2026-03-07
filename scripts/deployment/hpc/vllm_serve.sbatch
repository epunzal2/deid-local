#!/usr/bin/env bash
# ----------------
#SBATCH --job-name=vllm_serve
#SBATCH --output=logs/%x_%N_%j.out
#SBATCH --error=logs/%x_%N_%j.err
#SBATCH --partition=gpu-redhat
#SBATCH --gres=gpu:1
#SBATCH --constraint='volta|adalovelace|ampere'
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
# ----------------

set -euo pipefail

# --- Configurable parameters (all env-var driven, no hard-coded paths) ---
PROJECT_ROOT="${PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-$PWD}}"
VLLM_MODEL="${VLLM_MODEL:-meta-llama/Llama-3-8B-Instruct}"
VLLM_PORT="${VLLM_PORT:-8000}"
VLLM_HOST="${VLLM_HOST:-0.0.0.0}"
VLLM_MAX_MODEL_LEN="${VLLM_MAX_MODEL_LEN:-4096}"
VLLM_TENSOR_PARALLEL="${VLLM_TENSOR_PARALLEL:-1}"
VLLM_API_KEY="${VLLM_API_KEY:-}"
VLLM_DTYPE="${VLLM_DTYPE:-auto}"
VLLM_GPU_MEMORY_UTILIZATION="${VLLM_GPU_MEMORY_UTILIZATION:-0.90}"
VLLM_EXTRA_ARGS="${VLLM_EXTRA_ARGS:-}"
VLLM_HEALTH_TIMEOUT="${VLLM_HEALTH_TIMEOUT:-300}"
VLLM_ENDPOINT_DIR="${VLLM_ENDPOINT_DIR:-}"
CUDA_MODULE="${CUDA_MODULE:-cuda/12.1}"

cd "${PROJECT_ROOT}"
mkdir -p logs

export PYTHONUNBUFFERED=1

# --- Load CUDA module if available ---
if command -v module &>/dev/null; then
    echo "Loading module: ${CUDA_MODULE}"
    module load "${CUDA_MODULE}"
fi

# --- Activate virtual environment if present ---
if [[ -f "${PROJECT_ROOT}/.venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "${PROJECT_ROOT}/.venv/bin/activate"
fi

NODE_HOSTNAME="$(hostname -f)"
BASE_URL="http://${NODE_HOSTNAME}:${VLLM_PORT}"
HEALTH_URL="${BASE_URL}/health"

echo "=== vLLM Server Launch ==="
echo "Project root:  ${PROJECT_ROOT}"
echo "Node:          ${NODE_HOSTNAME}"
echo "SLURM Job ID:  ${SLURM_JOB_ID:-unknown}"
echo "Model:         ${VLLM_MODEL}"
echo "Port:          ${VLLM_PORT}"
echo "Tensor parallel: ${VLLM_TENSOR_PARALLEL}"
echo "Max model len: ${VLLM_MAX_MODEL_LEN}"
echo "GPU mem util:  ${VLLM_GPU_MEMORY_UTILIZATION}"
echo "Base URL:      ${BASE_URL}"
echo "CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-unset}"
echo ""

# --- Build vllm serve command ---
VLLM_CMD=(
    vllm serve "${VLLM_MODEL}"
    --host "${VLLM_HOST}"
    --port "${VLLM_PORT}"
    --dtype "${VLLM_DTYPE}"
    --max-model-len "${VLLM_MAX_MODEL_LEN}"
    --tensor-parallel-size "${VLLM_TENSOR_PARALLEL}"
    --gpu-memory-utilization "${VLLM_GPU_MEMORY_UTILIZATION}"
)

if [[ -n "${VLLM_API_KEY}" ]]; then
    VLLM_CMD+=(--api-key "${VLLM_API_KEY}")
fi

# shellcheck disable=SC2086
if [[ -n "${VLLM_EXTRA_ARGS}" ]]; then
    VLLM_CMD+=(${VLLM_EXTRA_ARGS})
fi

echo "Command: ${VLLM_CMD[*]}"
echo ""

# --- Launch server in the background ---
"${VLLM_CMD[@]}" &
VLLM_PID=$!

# --- Health polling loop ---
echo "Waiting for vLLM to become healthy (timeout: ${VLLM_HEALTH_TIMEOUT}s)..."
DEADLINE=$((SECONDS + VLLM_HEALTH_TIMEOUT))
HEALTHY=false

while [[ ${SECONDS} -lt ${DEADLINE} ]]; do
    if ! kill -0 "${VLLM_PID}" 2>/dev/null; then
        echo "ERROR: vLLM process exited before becoming healthy." >&2
        wait "${VLLM_PID}" || true
        exit 1
    fi
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}" 2>/dev/null || echo "000")
    if [[ "${HTTP_CODE}" -lt 400 && "${HTTP_CODE}" != "000" ]]; then
        HEALTHY=true
        break
    fi
    sleep 5
done

if [[ "${HEALTHY}" != "true" ]]; then
    echo "ERROR: vLLM failed to become healthy within ${VLLM_HEALTH_TIMEOUT}s." >&2
    kill "${VLLM_PID}" 2>/dev/null || true
    wait "${VLLM_PID}" || true
    exit 1
fi

echo ""
echo "=== vLLM Server Ready ==="
echo "Base URL:      ${BASE_URL}"
echo "Health URL:    ${HEALTH_URL}"
echo "Model:         ${VLLM_MODEL}"
echo "SLURM Job ID:  ${SLURM_JOB_ID:-unknown}"
echo ""

# --- Write endpoint discovery file ---
if [[ -n "${VLLM_ENDPOINT_DIR}" ]]; then
    mkdir -p "${VLLM_ENDPOINT_DIR}"
    ENDPOINT_FILE="${VLLM_ENDPOINT_DIR}/vllm-endpoint.json"
    cat > "${ENDPOINT_FILE}" <<ENDPOINT_JSON
{
  "base_url": "${BASE_URL}",
  "health_url": "${HEALTH_URL}",
  "model": "${VLLM_MODEL}",
  "node": "${NODE_HOSTNAME}",
  "port": ${VLLM_PORT},
  "slurm_job_id": "${SLURM_JOB_ID:-}",
  "started_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "api_key_required": $(if [[ -n "${VLLM_API_KEY}" ]]; then echo "true"; else echo "false"; fi)
}
ENDPOINT_JSON
    echo "Endpoint file written to: ${ENDPOINT_FILE}"
fi

# --- Keep the job alive until SLURM terminates it ---
echo "Server PID: ${VLLM_PID}. Waiting for process or SLURM timeout..."
wait "${VLLM_PID}"
