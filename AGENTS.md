# AGENTS.md

> Internal policy for the agent LLM that contributes to this repository.
> Human collaborators can ignore this file unless they want process details.

This file defines repo-wide operating rules so changes stay predictable, reviewable,
and safe.

## 0) Philosophy

- Automate over debate: enforce formatting, lint, and basic file checks with
  `pre-commit` and CI.
- Tests over throwaway scripts: experiments live in `scratch/` (gitignored) or become
  tests.
- Small, typed changes: prefer incremental PRs and clear public type hints.
- Reproducible setup: a newcomer should get running with one documented setup flow.
- Mixed development environments: support local macOS runs and Linux SLURM interactive
  runs during development, while keeping production deployment focused on the HPC
  cluster.

## 1) Repo map

- `pyproject.toml`: package metadata, dependency declarations, tool config, entry
  points.
- `.pre-commit-config.yaml`: formatter/linter/file guardrails used locally and in CI.
- `.editorconfig`: editor consistency (charset, line endings, indentation, final
  newline).
- `README.md`: project purpose, quickstart, and a minimal runnable example.
- `CONTRIBUTING.md`: contributor setup and PR workflow.
- `CHANGELOG.md`: Keep a Changelog style, SemVer-aware entries.
- `.plans/`: tracked implementation and design plans for higher-risk work.
- `src/<package>/`: shippable code only.
- `tests/`: unit and integration tests only.
- `scripts/`: thin wrappers that call code in `src/`.
- `docs/`: user docs and references.
- `examples/`: runnable usage examples.
- `scratch/`: gitignored prototypes and notebooks.

Environment conventions:
- Use `uv` as the default environment and dependency manager.
- Support `pip` as a documented fallback when `uv` is unavailable.
- Prefer a repo-local virtual environment such as `.venv/`; do not rely on Conda in
  this repository.
- Respect the repo's `.python-version` pin when creating or syncing environments, and
  prefer uv-managed Python builds over whatever interpreter happens to be active in the
  shell.
- Keep `requirements.txt` as the pip-compatible fallback install file generated from
  `uv.lock`.
- Keep `requirements-mac.txt` as the curated local macOS ML/LLM runtime install file.
- Keep `requirements-hpc.txt` as the curated Linux/NVIDIA HPC runtime install file.
- Install `llama-cpp-python` separately from the requirement files when backend-specific
  build flags such as Metal or CUDA must be passed.
- Keep machine-specific paths, scheduler options, and GPU settings in configuration or
  launch wrappers, not in core Python modules.

## 2) Product design

Create a short design note (1-2 pages) before major work.

Required sections:
- Problem (who/what/why now)
- Goals and non-goals (testable)
- User stories
- Solution sketch (sequence/diagram)
- Risks and alternatives
- Success metrics
- Rollout and back-compat
- Telemetry

Attach the note to an issue or PR and get one maintainer sign-off before large changes.

## 3) Project management

- Issues should include title, problem statement, acceptance criteria, and labels.
- Use milestones for multi-PR work and assign owners.
- Definition of Done: code + tests + docs + review + CI green.
- Triage regularly: close stale items, re-scope when needed, merge small PRs quickly.

## 4) Testing and quality gates

Layout: `src/<package>/...` and `tests/unit`, `tests/integration`, plus shared
`tests/conftest.py` when needed.

Rules:
- Test files: `test_*.py`; test names: `test_<behavior>()`.
- Prefer Arrange-Act-Assert and `pytest.mark.parametrize` over hand-written loops.
- Use fixtures for setup; keep tests declarative and fast.
- Mark long or external tests with `@pytest.mark.slow` and gate them in CI/nightly.
- New or changed code must include tests; optimize for critical-path coverage.
- Use property-based tests (`hypothesis`) for pure logic where useful.
- `ruff` is the required lint and formatting gate for Python code.
- Default setup:
  `uv sync --managed-python --python 3.12.9 --extra dev`
- `uv sync` creates the repo-local `.venv/` automatically.
- When `.venv/` was created by `uv`, install additional requirement files with
  `uv pip install ...` rather than `python -m pip install ...`.
- Install hooks with:
  `uv run pre-commit install`
- Run targeted checks for local edits:
  `uv run ruff check <path>` and `uv run ruff format <path>`
- Run broader validation before pushing:
  `uv run ruff check .`, `uv run ruff format --check .`, and `uv run pytest`
- Prefer staged-file mode for hooks:
  `uv run pre-commit run`
- `pip` fallback:
  `python -m venv .venv && source .venv/bin/activate &&
  python -m pip install -r requirements.txt`
- Local macOS runtime install:
  `python -m venv .venv && source .venv/bin/activate &&
  python -m pip install -r requirements-mac.txt`
- HPC GPU install:
  `python -m venv .venv && source .venv/bin/activate &&
  python -m pip install -r requirements-hpc.txt`
- Use explicit bootstrap scripts when environment-specific post-install steps are
  required, such as Metal or CUDA builds for `llama-cpp-python`.

## 5) Package management

- Use `pyproject.toml` (PEP 621) as the source of truth.
- Applications should pin direct dependencies for reproducibility.
- Libraries should use compatible version ranges and SemVer.
- Separate runtime and development dependencies.
- Keep the dependency graph lean and remove unused packages promptly.
- Expose CLIs through `project.scripts`.
- Commit lock artifacts when they are part of the supported workflow.
- Keep platform-specific GPU requirements in dedicated requirement files rather than
  mixing them into the base local development environment.

## 6) Git workflow

Branching:
- Feature: `feat/<scope>-<short-desc>`
- Fix: `fix/<scope>-<short-desc>`
- Keep branches short-lived and rebase on `main`.

Commits:
- Use Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`,
  `chore:`).
- Keep commits small and meaningful.
- Never commit generated binaries, model weights, or secrets.

Useful commands:
- `git switch -c ...`
- `git fetch && git rebase`
- `git commit --fixup ...`
- `git stash -u`
- `git bisect`

## 7) Markdown standards

- One H1 per file and a short opening summary.
- Wrap prose near 100 columns and avoid trailing spaces.
- Use fenced code blocks with language hints.
- Prefer reference-style links when reusing URLs.
- Keep tables simple and use Mermaid for diagrams when supported.
- Enforce markdown formatting, spell, and link checks in CI when docs become large
  enough to justify them.

## 8) Scripts

- Scripts live in `scripts/` and call into `src/` (no business logic in script
  wrappers).
- Every user-facing script must support `--help` and return sane exit codes.
- Write errors to stderr.
- Avoid interactive prompts in CI paths.
- Do not add throwaway test scripts; use `tests/` or `scratch/`.
- Prefer explicit names like `bootstrap_hpc.sh` over generic names like `setup.sh`
  when the script targets a specific environment.

## 9) Pull requests

Before opening:
- Run formatters, linters, and tests locally.
- Update docs and tests with code changes.
- Keep scope focused (soft cap: ~300 changed lines) unless the work is an approved
  scaffold or migration.

PR description:
- Why (problem)
- What (change)
- How (approach, migration, back-compat)
- Include CLI output or screenshots when relevant.

Review and merge:
- At least one maintainer review (two for risky changes).
- Address feedback with follow-up commits.
- Avoid force-push after review unless requested.
- Prefer squash merge.
- CI must be green.

## 10) Modules and layout

DO NOT READ `.env*` FILES.

Recommended structure:

```text
src/<package>/
  __init__.py
  __main__.py
  cli.py
  core/
  adapters/
  utils/
tests/
  unit/
  integration/
```

Rules:
- Keep one top-level package under `src/` and use absolute imports.
- `core` must not import from `adapters`.
- Avoid circular dependencies; refactor boundaries when they appear.
- Prefer typed exceptions and avoid catching bare `Exception`.
- Add type hints to public APIs.
- Keep macOS/local execution paths CPU-safe by default.
- Isolate GPU, scheduler, and cluster-specific logic behind adapters, config, or
  launch layers so local development remains testable.
- Treat Linux SLURM interactive sessions as a supported development and debugging path,
  not just a production-like environment.
- Do not hard-code CUDA device IDs, SLURM options, module commands, or cluster
  filesystem paths in reusable Python modules.
- Treat model weights, caches, checkpoints, and large generated artifacts as untracked
  runtime assets.

## 11) Documentation

- Keep docs under `docs/`.
- Use one docstring style consistently (Google or NumPy).
- Keep how-to guides short and copy/paste runnable.
- Commit diagram source files, not only rendered images.
- Maintain `CHANGELOG.md` for user-visible changes.
- CI should check docs builds and broken links when docs change enough to justify it.

## 12) Plans directory policy (`./.plans/`)

Purpose:
- Use plans for high-risk or cross-cutting changes so scope, risks, and rollout are
  explicit.

Canonical location decision:
- Use `./.plans/` as the canonical tracked location.
- Module-scoped `.plans/` directories are allowed only when the work is truly local to
  that module and the root plan would add noise.

When to create or update a plan:
- The user explicitly asks for a plan.
- Multi-module changes or new external dependencies.
- Public API breakage or migrations.
- Feature flags, rollback requirements, or deployment changes.
- Significant performance, security, privacy, or cluster/runtime changes.

Plan requirements:
- Create a Mermaid diagram in the plan that shows the end-to-end workflow of the
  proposed implementation.
- Use the filename format `YYYY-MM-DD-short-slug.md`.
- Include front matter with `Title`, `Status`, `Owner`, `Reviewers`, `Issues`, `Scope`,
  and `Risk`.

Minimum sections:
- Context & Problem
- Goals / Non-goals
- Design Overview
- Alternatives Considered
- Implementation Plan
- Data Model & Migrations (if any)
- Testing Strategy
- Rollout & Telemetry
- Risks & Mitigations
- Security & Privacy
- Docs to Update
- Rollback Plan
- Decision Log

Process:
1. Create or update the plan in `./.plans/`.
2. Keep `Status` and implementation checkboxes current.
3. On completion, set `Status: Done` and link the closing PR(s).
4. If scope changes materially, create a new plan and cross-link.

Plan milestone execution and commits:
- Implement plan-driven work in milestone-sized slices.
- Complete one milestone at a time: code, tests, and docs for that slice.
- Stage only files that belong to the completed milestone.
- Commit each milestone slice with a Conventional Commit message.
- Keep milestone commits runnable and reviewable; run impacted tests before moving to
  the next milestone.
- Squash merge remains preferred; milestone commits improve review and debugging quality
  during development.

## 13) Checklists

Contributor (before push):
- [ ] Lint and format checks pass
- [ ] Tests added or updated and pass locally
- [ ] Docs updated where needed
- [ ] No secrets, model weights, or large binaries committed

Maintainer (before merge):
- [ ] PR scope is focused and titled with Conventional Commit style
- [ ] Review feedback addressed
- [ ] CI green
- [ ] Back-compat and migration notes included
- [ ] Changelog updated for user-visible changes

## 14) HPC deployment practices

Config and execution:
- Keep cluster-specific launcher code, scheduler templates, and host assumptions out of
  `core/`.
- Prefer explicit config files or environment injection for CUDA, container, and queue
  settings.
- Support both macOS-local and Linux SLURM interactive runs during development and
  testing.
- Keep production deployment paths targeted at the Linux HPC cluster.

Operational guardrails:
- Never commit secrets, access tokens, SSH configs, or cluster-specific credentials.
- Never log raw credentials or private key material.
- Save manual verification artifacts under `verification/` with UTC timestamps when
  useful.

If any rule repeatedly slows delivery, open an issue with a concrete example so the
process can be improved.
