# Deployment

Deployment notes for the local `llama.cpp` path and the remote OpenAI-compatible
HPC path live here.

## Local `llama.cpp`

The default smoke-test model path is
`./models/llm/Phi-3-mini-4k-instruct-q4.gguf`. Keep that asset untracked.

### Setup

```bash
scripts/deployment/macos/setup_llama_cpp.sh
uv run deid-local model fetch
```

### Smoke test

```bash
uv run deid-local llm health --provider llama_cpp
uv run deid-local llm infer --provider llama_cpp --prompt "Reply with pong."
```

### End-to-end verification test

For a real macOS verification run against the active branch, use:

```bash
scripts/deployment/macos/verify_llama_cpp_e2e.sh
```

The wrapper prefers the current worktree's `.venv` and model asset, but it also
falls back to a sibling `../deid-local/.venv` and
`../deid-local/models/llm/Phi-3-mini-4k-instruct-q4.gguf` when you are working
from a feature worktree.

To run the underlying pytest directly:

```bash
export DEID_RUN_LLAMA_CPP_E2E=1
export DEID_E2E_MODEL_PATH=/absolute/path/to/Phi-3-mini-4k-instruct-q4.gguf
pytest tests/integration/test_llama_cpp_e2e.py -vv -s
```

### Local chat window

```bash
scripts/deployment/macos/run_chat_window.sh
```

By default the chat server binds to `http://127.0.0.1:8088`.

## Remote HTTP Providers

`deid-local` supports a generic `openai_http` client and a `vllm` preset.

### Common environment variables

```bash
export DEID_LLM_PROVIDER=vllm
export DEID_VLLM_BASE_URL=http://127.0.0.1:8000
export DEID_VLLM_MODEL=meta-llama/Llama-3-8B-Instruct
export DEID_VLLM_HEALTH_URL=http://127.0.0.1:8000/health
```

### Smoke test

```bash
uv run deid-local llm health --provider vllm
uv run deid-local llm infer --provider vllm --prompt "Reply with pong."
```

## SLURM Wrappers

The HPC wrappers are intentionally generic. They rely on `uv`, repo-relative
paths, and environment variables instead of hard-coded usernames, Conda
environments, or scratch directories.

### Prepare the environment

```bash
scripts/deployment/hpc/setup_env.sh
```

### Submit the `llama.cpp` smoke job

```bash
sbatch scripts/deployment/hpc/llama_cpp_smoke.sbatch
```

or:

```bash
scripts/deployment/hpc/submit_llama_cpp_smoke.sh
```

### Submit the `vllm` smoke job

```bash
sbatch scripts/deployment/hpc/vllm_smoke.sbatch
```

or:

```bash
scripts/deployment/hpc/submit_vllm_smoke.sh
```

## Config Resolution

Runtime settings resolve in this order:

1. CLI flags
2. `DEID_*` environment variables
3. supported legacy aliases
4. code defaults

The most important settings are:

- `DEID_LLM_PROVIDER`
- `DEID_LLAMA_MODEL_PATH`
- `DEID_OPENAI_BASE_URL`
- `DEID_OPENAI_MODEL`
- `DEID_OPENAI_HEALTH_URL`
- `DEID_VLLM_BASE_URL`
- `DEID_VLLM_MODEL`
- `DEID_VLLM_HEALTH_URL`

Use `uv run deid-local llm config` to inspect the resolved settings without
exposing API keys.
