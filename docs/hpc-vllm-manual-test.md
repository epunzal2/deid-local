# HPC vLLM Manual Test Runbook

This runbook provides copy-paste commands for manual HPC validation and lists the key
outputs to relay back after each step.

## Test Inputs

Fill these once before running commands:

```bash
export PROJECT_ROOT="$(pwd)"
export SHARED_MODEL_DIR="${PROJECT_ROOT}/models/llm/Llama-3-8B-Instruct"
export VLLM_ENDPOINT_DIR="${PROJECT_ROOT}/models/llm/vllm-endpoints"
export VLLM_API_KEY="$(openssl rand -hex 32)"
mkdir -p "${SHARED_MODEL_DIR}" "${VLLM_ENDPOINT_DIR}"
```

## Step 1: Validate environment

```bash
scripts/deployment/hpc/setup_env.sh
```

Expected:

- Prints "Base HPC environment is ready."
- No install errors.

Relay back:

- Any non-zero exit code.
- Last 20 lines if dependencies fail to install.

## Step 2: Download model snapshot

Run this step on a login/data-transfer node:

```bash
scripts/deployment/hpc/download_vllm_model.sh \
  --repo-id meta-llama/Llama-3-8B-Instruct \
  --output-dir "${SHARED_MODEL_DIR}"
```

Expected:

- Prints model snapshot path.
- `${SHARED_MODEL_DIR}` contains files like `config.json`, tokenizer files, and weights.

Relay back:

- Full command output.
- `ls -la "${SHARED_MODEL_DIR}" | head -n 20`.

## Step 3: Submit vLLM serve job

```bash
scripts/deployment/hpc/submit_vllm_serve.sh \
  --model "${SHARED_MODEL_DIR}" \
  --gpus 1 \
  --partition gpu-redhat \
  --time 04:00:00 \
  --port 8000 \
  --endpoint-dir "${VLLM_ENDPOINT_DIR}" \
  --api-key "${VLLM_API_KEY}"
```

Expected:

- Prints `Submitted batch job <job_id>`.
- Shows `Track status with: squeue -j <job_id>`.

Relay back:

- The full submit output.
- The `<job_id>` value.

## Step 4: Wait for health and endpoint file

```bash
scripts/deployment/hpc/check_vllm_status.sh --endpoint-dir "${VLLM_ENDPOINT_DIR}"
```

Expected:

- `healthy: true`
- `slurm_state: RUNNING`
- endpoint metadata fields printed

Relay back:

- Entire status output.
- If unhealthy: `logs/vllm_serve_*_<job_id>.out` and `.err` tail.

## Step 5: Connect and verify client health

```bash
uv run llm-local llm connect \
  --endpoint-dir "${VLLM_ENDPOINT_DIR}" \
  --api-key "${VLLM_API_KEY}" \
  --test
```

Expected:

- Prints `export ...` lines for `LLM_PROVIDER` and `VLLM_*`.
- Prints `Health probe succeeded ...`.

Relay back:

- Entire command output.

## Step 6: Run inference

```bash
eval "$(uv run llm-local llm connect --endpoint-dir "${VLLM_ENDPOINT_DIR}" --api-key "${VLLM_API_KEY}")"
uv run llm-local llm infer --provider vllm --prompt "Reply with pong."
```

Expected:

- Non-empty completion response.
- Includes `pong` or a semantically correct short response.

Relay back:

- Exact inference output text.

## Step 7: Check aggregate status

```bash
uv run llm-local llm status --endpoint-dir "${VLLM_ENDPOINT_DIR}" --api-key "${VLLM_API_KEY}"
```

Expected:

- `Health: healthy`
- `SLURM state: RUNNING`
- non-empty model info or served model IDs

Relay back:

- Entire status output.

## Step 8: Stop service and cleanup endpoint

```bash
scripts/deployment/hpc/stop_vllm_serve.sh --endpoint-dir "${VLLM_ENDPOINT_DIR}"
```

Expected:

- `Cancelled SLURM job: <job_id>` or clear cancellation warning.
- `Removed endpoint file: .../vllm-endpoint.json`

Relay back:

- Entire stop output.
- `ls -la "${VLLM_ENDPOINT_DIR}"`.

## Optional: Save verification artifact log

```bash
scripts/deployment/hpc/verify_vllm_serve.sh
```

Expected:

- Writes a timestamped log under `verification/`.

Relay back:

- The generated log path.
- Any failed test names if the script exits non-zero.
