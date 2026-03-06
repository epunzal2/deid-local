# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Initial repository scaffold with `uv`/`pip` setup instructions, `ruff`, `pytest`,
  `pre-commit`, a minimal CLI, and root-level `.plans/` support.
- MIT `LICENSE` file and matching package metadata.
- Generated `requirements.txt` as the pip-compatible install file exported from
  `uv.lock`.
- Added `requirements-mac.txt` for the local macOS ML/LLM runtime stack.
- Added `requirements-hpc.txt` for the Linux/NVIDIA HPC runtime stack, including the
  core LLM and GPU Python dependencies.
- Moved `llama-cpp-python` to explicit post-install commands so Metal/CUDA build flags
  are applied correctly.
- Added `scripts/bootstrap_hpc.sh` as the explicit HPC environment bootstrap helper.
- Added `scripts/bootstrap_mac.sh` as the explicit macOS environment bootstrap helper.
- Updated the macOS bootstrap flow to install experimental Apple Silicon `vllm` from
  source and aligned `requirements-mac.txt` with the working package versions.
- Typed LLM runtime settings, local `llama.cpp` and OpenAI-compatible provider
  adapters, and health-check helpers.
- `llm-local llm ...` and `llm-local model ...` CLI surfaces for config,
  health, inference, download, and verification.
- Generic local/HPC deployment wrappers plus deployment documentation for the
  default `./models/llm/Phi-3-mini-4k-instruct-q4.gguf` smoke-test model.
- A local Flask-backed browser chat window for smoke testing the configured LLM
  provider without bringing in the older RAG chat UI.
- An opt-in macOS end-to-end `llama.cpp` verification test and wrapper that can
  reuse a sibling main worktree's `.venv` and model asset.
- An opt-in macOS CPU `vllm` end-to-end verification test and wrapper that
  starts a local OpenAI-compatible `vllm serve` process using
  `./models/llm/opt-125m`.
- HPC vLLM serving wrappers:
  `scripts/deployment/hpc/submit_vllm_serve.sh`,
  `scripts/deployment/hpc/vllm_serve.sbatch`,
  `scripts/deployment/hpc/check_vllm_status.sh`,
  `scripts/deployment/hpc/stop_vllm_serve.sh`, and
  `scripts/deployment/hpc/fetch_model.sh`.
- Endpoint discovery support with `vllm-endpoint.json` handling in
  `llm_local.core.endpoint_discovery`.
- `llm-local llm connect` for endpoint discovery and export command generation.
- `llm-local llm status` with aggregated health, model info, and SLURM state.
- `llm-local model fetch-hf` for Hugging Face snapshot download with optional
  token and revision selection.
- Additional integration and unit coverage:
  `tests/integration/test_concurrent_requests.py`,
  `tests/unit/test_server_status.py`, and
  `tests/unit/test_slurm_scripts.py`.
- HPC verification wrapper `scripts/deployment/hpc/verify_vllm_serve.sh` with
  timestamped logs under `verification/`.
- New HPC docs:
  `docs/hpc-vllm-guide.md` and `docs/hpc-vllm-manual-test.md`, with
  `docs/deployment.md` updated to link the runbooks.
