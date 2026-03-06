# deid-local

Local-first Python scaffolding for LLM workflows that are developed on a MacBook and
then promoted to a Linux HPC environment with GPU access.

The repository now provides a typed deployment substrate for local `llama.cpp`
smoke tests and remote OpenAI-compatible HTTP inference, plus generic SLURM
launcher wrappers for HPC smoke validation.

## Quickstart

### Preferred: `uv`

```bash
uv sync --managed-python --python 3.12.9 --extra dev
uv pip install -r requirements-mac.txt
CMAKE_ARGS="-DGGML_METAL=on" FORCE_CMAKE=1 \
  uv pip install --no-binary llama-cpp-python llama-cpp-python
git clone https://github.com/vllm-project/vllm.git scratch/vllm-source
uv pip install -r scratch/vllm-source/requirements/cpu.txt
VLLM_TARGET_DEVICE=cpu uv pip install -e scratch/vllm-source
uv run pre-commit install
uv run pytest
uv run deid-local doctor
```

`uv sync` creates the repo-local `.venv/` automatically. When that environment was
created by `uv`, install additional requirement files with `uv pip ...`, not
`python -m pip ...`.

### Fallback: `pip`

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pre-commit install
pytest
deid-local doctor
```

### Local macOS runtime stack

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-mac.txt
CMAKE_ARGS="-DGGML_METAL=on" FORCE_CMAKE=1 \
  python -m pip install --no-binary llama-cpp-python llama-cpp-python
git clone https://github.com/vllm-project/vllm.git scratch/vllm-source
python -m pip install -r scratch/vllm-source/requirements/cpu.txt
VLLM_TARGET_DEVICE=cpu python -m pip install -e scratch/vllm-source
```

If your current `.venv` was created by `uv`, use:

```bash
uv pip install -r requirements-mac.txt
CMAKE_ARGS="-DGGML_METAL=on" FORCE_CMAKE=1 \
  uv pip install --no-binary llama-cpp-python llama-cpp-python
git clone https://github.com/vllm-project/vllm.git scratch/vllm-source
uv pip install -r scratch/vllm-source/requirements/cpu.txt
VLLM_TARGET_DEVICE=cpu uv pip install -e scratch/vllm-source
```

Or use the helper script:

```bash
scripts/bootstrap_mac.sh --help
scripts/bootstrap_mac.sh
```

### HPC GPU environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-hpc.txt
CMAKE_ARGS="-DGGML_CUDA=on" FORCE_CMAKE=1 \
  python -m pip install --no-binary llama-cpp-python llama-cpp-python
```

Or use the helper script:

```bash
scripts/bootstrap_hpc.sh --help
scripts/bootstrap_hpc.sh
```

## LLM Deployment Surface

The default smoke-test model path is
`./models/llm/Phi-3-mini-4k-instruct-q4.gguf`.

### Local `llama.cpp`

```bash
scripts/deployment/macos/setup_llama_cpp.sh
uv run deid-local model fetch
uv run deid-local llm health --provider llama_cpp
uv run deid-local llm infer --provider llama_cpp --prompt "Reply with pong."
scripts/deployment/macos/verify_llama_cpp_e2e.sh
scripts/deployment/macos/run_chat_window.sh
```

### Remote `vllm`

```bash
export DEID_LLM_PROVIDER=vllm
export DEID_VLLM_BASE_URL=http://127.0.0.1:8000
export DEID_VLLM_MODEL=meta-llama/Llama-3-8B-Instruct
export DEID_VLLM_HEALTH_URL=http://127.0.0.1:8000/health

uv run deid-local llm config
uv run deid-local llm health
uv run deid-local llm infer --prompt "Reply with pong."
```

More detail lives in [`docs/deployment.md`](./docs/deployment.md).

## Development workflow

Use local macOS runs and Linux SLURM interactive runs as development and testing
workflows. Keep Linux HPC and GPU-specific behavior behind adapters or launch wrappers
so the core package stays testable on a laptop while still supporting cluster-side
debugging. Production deployment is expected to run on the HPC cluster. The repository
pins Python via [`.python-version`](./.python-version), and the `--managed-python`
setup command keeps `uv` from reusing a Conda interpreter from your shell.
[`requirements.txt`](./requirements.txt) is the pip-compatible fallback generated from
`uv.lock`. [`requirements-mac.txt`](./requirements-mac.txt) is the local macOS ML/LLM
runtime stack. [`requirements-hpc.txt`](./requirements-hpc.txt) is the Linux/NVIDIA
HPC runtime stack for cluster installs. `llama-cpp-python` and macOS `vllm` are
installed as separate steps so Metal and source-build settings can be applied
correctly.

Before larger or riskier changes, add a plan in [`./.plans/`](./.plans/) using the
repository template.

## Common commands

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run deid-local --help
uv run deid-local doctor
uv run deid-local llm config
uv run deid-local model verify
```

## Repository layout

```text
.plans/               Implementation and design plans
docs/                 Project documentation
examples/             Runnable examples
scripts/              Thin wrappers around package code
src/deid_local/       Application package
tests/                Unit and integration tests
```

## Next steps

- Expand provider coverage only when a concrete runtime needs it.
