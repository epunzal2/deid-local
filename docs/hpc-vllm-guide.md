# HPC vLLM Guide

This guide covers the end-to-end HPC workflow for serving a shared vLLM endpoint and
connecting clients with `llm-local`.

## Prerequisites

- Access to your HPC cluster's GPU partition and a project directory with enough space.
- Use the RHEL9 GPU partition (`gpu-redhat`) for serve and validation jobs.
- `uv` and SLURM commands (`sbatch`, `squeue`, `scancel`) available on the cluster.
- Repository checked out on shared storage.
- A repo-local virtual environment with dependencies installed.
- Review [HPC GLIBC and Partition Compatibility Note](./hpc-glibc-partition-note.md).

Bootstrap command:

```bash
scripts/deployment/hpc/setup_env.sh
```

## Quickstart

### 1. Choose shared directories

Pick paths that all users can read:

```bash
export PROJECT_ROOT="$(pwd)"
export SHARED_MODEL_DIR="${PROJECT_ROOT}/models/llm/Llama-3-8B-Instruct"
export VLLM_ENDPOINT_DIR="${PROJECT_ROOT}/models/llm/vllm-endpoints"
mkdir -p "${SHARED_MODEL_DIR}" "${VLLM_ENDPOINT_DIR}"
```

Use a true group/shared filesystem path instead of repo-local paths when multiple users
or nodes need stable access.

### 2. Download model snapshot

```bash
scripts/deployment/hpc/fetch_model.sh \
  --repo-id meta-llama/Llama-3-8B-Instruct \
  --output-dir "${SHARED_MODEL_DIR}"
```

If auth is required:

```bash
export HF_TOKEN="<your-hf-token>"
```

### 3. Launch vLLM service

```bash
scripts/deployment/hpc/submit_vllm_serve.sh \
  --model "${SHARED_MODEL_DIR}" \
  --gpus 1 \
  --partition gpu-redhat \
  --time 04:00:00 \
  --port 8000 \
  --endpoint-dir "${VLLM_ENDPOINT_DIR}" \
  --api-key "<shared-api-key>"
```

This submits `scripts/deployment/hpc/vllm_serve.sbatch` and writes
`${VLLM_ENDPOINT_DIR}/vllm-endpoint.json` after health passes.

### 4. Check service status

```bash
scripts/deployment/hpc/check_vllm_status.sh --endpoint-dir "${VLLM_ENDPOINT_DIR}"
```

Optional CLI aggregate status:

```bash
uv run llm-local llm status --endpoint-dir "${VLLM_ENDPOINT_DIR}" --api-key "<shared-api-key>"
```

### 5. Connect clients and test inference

Print export commands and run a probe:

```bash
uv run llm-local llm connect \
  --endpoint-dir "${VLLM_ENDPOINT_DIR}" \
  --api-key "<shared-api-key>" \
  --test
```

Load resolved endpoint values into your shell:

```bash
eval "$(uv run llm-local llm connect --endpoint-dir "${VLLM_ENDPOINT_DIR}" --api-key "<shared-api-key>")"
```

Run inference:

```bash
uv run llm-local llm infer --provider vllm --prompt "Reply with pong."
```

### 6. Stop service and clean endpoint

```bash
scripts/deployment/hpc/stop_vllm_serve.sh --endpoint-dir "${VLLM_ENDPOINT_DIR}"
```

## Environment Variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `LLM_PROVIDER` | Default provider selection | `llama_cpp` |
| `VLLM_BASE_URL` | vLLM HTTP base URL | `http://127.0.0.1:8000` |
| `VLLM_HEALTH_URL` | vLLM health endpoint | `http://127.0.0.1:8000/health` |
| `VLLM_MODEL` | Model ID or model path for HTTP requests | `meta-llama/Llama-3-8B-Instruct` |
| `VLLM_API_KEY` | Bearer token for vLLM OpenAI-compatible API | unset |
| `VLLM_ENDPOINT_DIR` | Shared endpoint metadata directory | unset |
| `VLLM_PORT` | vLLM service port | `8000` |
| `VLLM_HOST` | vLLM bind host | `0.0.0.0` |
| `VLLM_TENSOR_PARALLEL` | Tensor parallel shard count | `1` |
| `VLLM_MAX_MODEL_LEN` | Max context length | `4096` |
| `VLLM_GPU_MEMORY_UTILIZATION` | GPU memory target fraction | `0.90` |
| `VLLM_DTYPE` | vLLM dtype setting | `auto` |
| `VLLM_HEALTH_TIMEOUT` | Startup health timeout (seconds) | `300` |
| `VLLM_EXTRA_ARGS` | Additional `vllm serve` args | unset |
| `CUDA_MODULE` | CUDA module loaded by `vllm_serve.sbatch` | `cuda/12.1` |
| `HF_TOKEN` | Hugging Face token used by `fetch-hf` | unset |

## GPU-Specific Notes

- A100 40G: typically works with `--gpus 1` and default model length.
- L40S 40G: similar tuning to A100 for Llama 3 8B.
- V100 32G: may need lower context window:
  - add `--max-model-len 2048` when submitting.
  - optionally lower `VLLM_GPU_MEMORY_UTILIZATION` to reduce OOM risk.

For multi-GPU serve, increase `--gpus` in `submit_vllm_serve.sh`; this also sets
`VLLM_TENSOR_PARALLEL`.

## Troubleshooting

- Endpoint file missing:
  - verify `--endpoint-dir` on submit command.
  - inspect SLURM log under `logs/vllm_serve_<node>_<job>.out`.
- Health probe fails:
  - check `check_vllm_status.sh` output and HTTP status code.
  - ensure firewall/network allows node-to-node HTTP on the configured port.
- 401 Unauthorized:
  - ensure matching `VLLM_API_KEY` or `--api-key` on client commands.
- OOM or startup crash:
  - reduce `--max-model-len`.
  - lower `VLLM_GPU_MEMORY_UTILIZATION`.
  - verify GPU type and available memory.
- `GLIBC_x.y not found` import error on GPU node:
  - compare login-node and compute-node glibc versions.
  - submit to `gpu-redhat` to stay on the RHEL9 GPU partition.
  - see [HPC GLIBC and Partition Compatibility Note](./hpc-glibc-partition-note.md).
