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
- `deid-local llm ...` and `deid-local model ...` CLI surfaces for config,
  health, inference, download, and verification.
- Generic local/HPC deployment wrappers plus deployment documentation for the
  default `./models/llm/Phi-3-mini-4k-instruct-q4.gguf` smoke-test model.
- A local Flask-backed browser chat window for smoke testing the configured LLM
  provider without bringing in the older RAG chat UI.
