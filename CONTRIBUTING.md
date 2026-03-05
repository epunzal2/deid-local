# Contributing

Contributor setup and workflow for `deid-local`.

## Setup

### Preferred: `uv`

```bash
uv sync --managed-python --python 3.12.9 --extra dev
uv run pre-commit install
```

### Fallback: `pip`

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pre-commit install
```

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
