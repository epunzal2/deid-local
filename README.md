# deid-local

Local-first Python scaffolding for LLM workflows that are developed on a MacBook and
then promoted to a Linux HPC environment with GPU access.

The repository currently provides a clean baseline: packaging, linting, tests,
planning conventions, and a small CLI surface for environment checks.

## Quickstart

### Preferred: `uv`

```bash
uv sync --managed-python --python 3.12.9 --extra dev
uv run pre-commit install
uv run pytest
uv run deid-local doctor
```

### Fallback: `pip`

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pre-commit install
pytest
deid-local doctor
```

## Development workflow

Use local macOS runs and Linux SLURM interactive runs as development and testing
workflows. Keep Linux HPC and GPU-specific behavior behind adapters or launch wrappers
so the core package stays testable on a laptop while still supporting cluster-side
debugging. Production deployment is expected to run on the HPC cluster. The repository
pins Python via [`.python-version`](./.python-version), and the `--managed-python`
setup command keeps `uv` from reusing a Conda interpreter from your shell.

Before larger or riskier changes, add a plan in [`./.plans/`](./.plans/) using the
repository template.

## Common commands

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run deid-local --help
uv run deid-local doctor
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

- Add the first concrete runtime/backend adapter under `src/deid_local/adapters/`.
- Add cluster submission or job-launch wrappers under `scripts/` once the target SLURM
  workflow is known.
- Expand `docs/` with deployment notes when the local execution path stabilizes.
