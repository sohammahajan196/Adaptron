# Contributing to Adaptron

Adaptron is developed phase-by-phase, as tracked in [TASKS.md](./TASKS.md) and designed in [PLAN.md](./PLAN.md). This guide covers how to set up a development environment and the workflow contributions are expected to follow, once implementation begins.

## Development setup

```bash
git clone https://github.com/<org>/adaptron.git
cd adaptron
pip install -e ".[langchain,crewai,dev]"   # editable install with all extras + dev tooling
pre-commit install
```

`dev` is expected to include `pytest`, `ruff`, and `mypy` (see [PLAN.md §5](./PLAN.md)).

## Running checks locally

```bash
pytest                 # core tests (run with no extras installed to verify dependency isolation)
pytest --run-bridges   # if a marker/flag is added to opt into bridge tests explicitly
ruff check .
ruff format --check .
mypy adaptron/core
```

All four should pass before opening a pull request — they mirror the CI jobs in `.github/workflows/ci.yml`.

## Workflow

- **One phase per branch/PR.** Each phase in [TASKS.md](./TASKS.md) (aligned with [PLAN.md §3](./PLAN.md)) should land as its own pull request with its own tests, rather than being bundled with unrelated work. Large phases may also ship as one PR per Task X.Y.
- **Tests are required, not optional.** A phase isn't done until its Phase Completion Checklist in `TASKS.md` is satisfied and its tests pass in CI.
- **Core stays dependency-free.** Nothing under `adaptron/core/` may import `langchain`, `crewai`, or any other optional dependency, even conditionally. Framework-specific code belongs in `adaptron/bridges/` only (see [STRUCTURE.md](./STRUCTURE.md)).
- **Errors must be actionable.** Any new exception should name the failing stage and the offending input/types, per the `Debuggability` requirement in [PRD.md §7](./PRD.md).
- **Update `CHANGELOG.md`** for any user-facing change, following [Keep a Changelog](https://keepachangelog.com/) format.

## Reporting issues

When filing a bug, include: the Adaptron version, the minimal pipeline that reproduces the issue, and the full error message or log output (verbose mode) if the pipeline runs but produces an unexpected result.

## Proposing new features

If your proposal isn't already covered by [PRD.md §12](./PRD.md) (Future Considerations) or [PLAN.md §7](./PLAN.md) (Deferred design decisions), open an issue describing the use case before submitting a PR — this keeps the core scope-disciplined per the project's [non-goals](./PRD.md).
