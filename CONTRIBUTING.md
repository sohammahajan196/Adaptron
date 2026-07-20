# Contributing to Adaptron

Adaptron is developed phase-by-phase, as tracked in [TASKS.md](./TASKS.md) and
designed in [PLAN.md](./PLAN.md). This guide covers how to set up a development
environment and the workflow contributions are expected to follow.

## Development setup

Requires **Python 3.10+**.

```bash
git clone https://github.com/<org>/adaptron.git
cd adaptron
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[langchain,crewai,dev]"   # editable install with all extras + dev tooling
pre-commit install
```

`dev` includes `pytest`, `ruff`, `mypy`, and `pre-commit` (see [PLAN.md §5](./PLAN.md)
and `pyproject.toml`).

## Running checks locally

Run these from the repository root. They mirror
[`.github/workflows/ci.yml`](./.github/workflows/ci.yml).

**Core job** (bare package — no LangChain/CrewAI extras):

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy adaptron/core      # run in a venv WITHOUT langchain/crewai installed — see note below
pytest
```

**Bridge tests** (install bridge extras first):

```bash
pip install -e ".[langchain,crewai,dev]"
pytest tests/test_bridges_*.py
```

**`mypy` must be run in a venv without the `langchain`/`crewai` extras
installed**, even though `mypy adaptron/core` never imports either package.
mypy statically follows every `import langchain` / `import crewai` it finds —
including the lazy, `try`/`except`-guarded ones in `adaptron/__init__.py` and
`adaptron/bridges/*.py` — regardless of whether that import is actually
reachable at runtime. If those packages happen to be installed in the same
environment, mypy resolves them for real and can fail on unrelated
transitive-dependency stub issues that have nothing to do with Adaptron's own
code. `[tool.mypy] packages` in `pyproject.toml` is scoped to `adaptron.core`
for the same reason — the bridges are intentionally excluded from routine
mypy runs (see `pyproject.toml`'s `[tool.mypy]` comment).

All checks above should pass before opening a pull request. CI runs on every
pull request (and on `main`/`master` pushes) with three jobs:

1. **Core tests** — bare package + `pytest` / `ruff` / `mypy` (matrix: Python 3.10–3.12)
2. **Bridge tests** — installs `adaptron[langchain,crewai]` and runs `tests/test_bridges_*.py`
3. **Dependency isolation** — bare install must leave `langchain` and `crewai` importable-absent

## Workflow

- **One phase per branch/PR.** Each phase in [TASKS.md](./TASKS.md) (aligned with [PLAN.md §3](./PLAN.md)) should land as its own pull request with its own tests, rather than being bundled with unrelated work. Large phases may also ship as one PR per Task X.Y.
- **Tests are required, not optional.** A phase isn't done until its Phase Completion Checklist in `TASKS.md` is satisfied and its tests pass in CI.
- **Core stays dependency-free.** Nothing under `adaptron/core/` may import `langchain`, `crewai`, or any other optional dependency, even conditionally. Framework-specific code belongs in `adaptron/bridges/` only (see [STRUCTURE.md](./STRUCTURE.md)).
- **Errors must be actionable.** Prefer the existing hierarchy — `WrapError`,
  `NoAdapterError`, `PipelineExecutionError` (all under `AdaptronError`) —
  rather than bare stdlib exceptions. Messages should name the failing
  stage/adapter, the offending input (preview) and types when relevant, and
  a concrete fix when one exists (e.g. the exact `register_adapter(...)`
  call), per the `Debuggability` requirement in [PRD.md §7](./PRD.md).
  Adapter callables that raise mid-`run()` must be wrapped as
  `PipelineExecutionError` — never left as a raw opaque traceback alone.
- **Update `CHANGELOG.md`** for any user-facing change, following [Keep a Changelog](https://keepachangelog.com/) format.

## Reporting issues

When filing a bug, include: the Adaptron version, the minimal pipeline that reproduces the issue, and the full error message or log output (verbose mode) if the pipeline runs but produces an unexpected result.

## Proposing new features

If your proposal isn't already covered by [PRD.md §12](./PRD.md) (Future Considerations) or [PLAN.md §7](./PLAN.md) (Post-v1 decisions made), open an issue describing the use case before submitting a PR — this keeps the core scope-disciplined per the project's [non-goals](./PRD.md).
