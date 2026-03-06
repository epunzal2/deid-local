# Contributing

Contributor setup and workflow for `deid-local`.

## Setup

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
```

`uv sync` creates the repo-local `.venv/` automatically. Use `uv pip ...` for extra
requirements in that environment.

### Fallback: `pip`

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pre-commit install
```

### Local macOS runtime install

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

### HPC GPU install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-hpc.txt
CMAKE_ARGS="-DGGML_CUDA=on" FORCE_CMAKE=1 \
  python -m pip install --no-binary llama-cpp-python llama-cpp-python
```

The preferred cluster helper is `scripts/bootstrap_hpc.sh`, not a generic top-level
`setup.sh`, because the name makes the target environment explicit and leaves room for
future platform-specific bootstrap scripts. Use `scripts/bootstrap_mac.sh` for the
macOS runtime stack when you want the same behavior locally.

## Daily commands

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run pre-commit run
```

If you are using the `pip` fallback, activate `.venv` and run the same commands without
the `uv run` prefix.

Development testing can happen either on local macOS or in Linux SLURM interactive
sessions. Keep production deployment assumptions isolated to the HPC cluster paths and
launchers.

## Plans

Create or update a plan in [`./.plans/`](./.plans/) before multi-module, deployment,
or otherwise high-risk work. Follow the template and keep the status/checklists current.

## Pull requests

- Use Conventional Commits.
- Keep PRs focused and reviewable.
- Update tests and docs with behavior changes.
- Do not commit secrets, model weights, checkpoints, or large generated artifacts.
