# Deployment

Deployment documentation for local verification and HPC vLLM serving lives here.

## Local `llama.cpp`

The default smoke-test model path is `./models/llm/Phi-3-mini-4k-instruct-q4.gguf`.

### Setup

```bash
scripts/deployment/macos/setup_llama_cpp.sh
uv run llm-local model fetch
```

### Smoke test

```bash
uv run llm-local llm health --provider llama_cpp
uv run llm-local llm infer --provider llama_cpp --prompt "Reply with pong."
```

### End-to-end verification

```bash
scripts/deployment/macos/verify_llama_cpp_e2e.sh
```

To run the underlying test directly:

```bash
export RUN_LLAMA_CPP_E2E=1
pytest tests/integration/test_llama_cpp_e2e.py -vv -s
```

## Local macOS `vllm` CPU verification

This path validates local client/server behavior, not HPC parity.

```bash
huggingface-cli download facebook/opt-125m --local-dir ./models/llm/opt-125m --local-dir-use-symlinks False
scripts/deployment/macos/verify_vllm_e2e.sh
```

## HPC vLLM serving

For full setup and operations:

- [HPC vLLM Guide](./hpc-vllm-guide.md)
- [HPC vLLM Manual Test Runbook](./hpc-vllm-manual-test.md)
- [HPC GLIBC and Partition Compatibility Note](./hpc-glibc-partition-note.md)

Key wrapper commands:

```bash
scripts/deployment/hpc/setup_env.sh
scripts/deployment/hpc/fetch_model.sh --help
scripts/deployment/hpc/submit_vllm_serve.sh --help
scripts/deployment/hpc/check_vllm_status.sh --help
scripts/deployment/hpc/stop_vllm_serve.sh --help
scripts/deployment/hpc/verify_vllm_serve.sh --help
```

## Config resolution

Runtime settings resolve in this order:

1. CLI flags
2. Environment variables
3. Code defaults

Core variables:

- `LLM_PROVIDER`
- `LLAMA_MODEL_PATH`
- `VLLM_BASE_URL`
- `VLLM_MODEL`
- `VLLM_HEALTH_URL`
- `VLLM_API_KEY`
- `VLLM_ENDPOINT_DIR`

Use `uv run llm-local llm config` to inspect resolved settings without exposing
credentials.
