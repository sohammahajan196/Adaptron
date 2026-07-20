# Project Folder Structure

This document lays out the full repository layout implied by [PLAN.md](./PLAN.md) and [PRD.md](./PRD.md), with a short explanation of every folder and major file. It is the reference map of the shipped **v0.1.0** repository (Phases 0–9 complete; see [TASKS.md](./TASKS.md)). For *how* the core modules work internally (data model, resolution algorithms, milestone details), see [PLAN.md §2-3](./PLAN.md) — this document only covers *what lives where and why it's organized that way*, to avoid repeating that content.

```
adaptron/
├── PRD.md
├── PLAN.md
├── STRUCTURE.md
├── TASKS.md
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml
├── .pre-commit-config.yaml
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── .cursor/
│   └── rules/
│       ├── core.mdc
│       ├── architecture.mdc
│       ├── dependencies.mdc
│       ├── ai-workflow.mdc
│       ├── python-standards.mdc
│       ├── error-handling.mdc
│       ├── performance.mdc
│       ├── bridges.mdc
│       ├── testing.mdc
│       └── documentation.mdc
├── adaptron/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── pipeline.py
│   │   ├── adapters.py
│   │   ├── logging.py
│   │   └── errors.py
│   └── bridges/
│       ├── __init__.py
│       ├── langchain_bridge.py
│       └── crewai_bridge.py
├── examples/
│   ├── plain_python_pipeline.py
│   └── cross_framework_pipeline.py
├── docs/
│   ├── demo-flagship.svg
│   └── playground/
└── tests/
    ├── test_agent.py
    ├── test_pipeline.py
    ├── test_adapters.py
    ├── test_logging.py
    ├── test_bridges_langchain.py
    ├── test_bridges_crewai.py
    ├── test_errors.py
    ├── test_examples.py
    └── test_post_v1.py
```

---

## Root level

- **`PRD.md`** — the product requirements: problem statement, goals, personas, user stories, functional/non-functional requirements, success metrics, risks, and post-v1 considerations. The source of truth for *what* and *why*.
- **`PLAN.md`** — the technical architecture: repo layout summary, core data model (`Agent`, `Pipeline`, adapter registry, bridges), milestone-by-milestone implementation notes, testing/CI strategy, and packaging. The source of truth for *how* the system is built.
- **`STRUCTURE.md`** — this file; keeps the intended repo layout explicit and reviewable, and explains the placement rationale for each file/folder.
- **`TASKS.md`** — the phase-based implementation roadmap. Where `PLAN.md`'s milestones describe *what each milestone must achieve architecturally*, `TASKS.md` turns them into Phases 0–9 with session-sized tasks (goal, files, dependencies, acceptance criteria, subtasks). `PLAN.md` stays stable as a reference; `TASKS.md` is expected to change constantly as work proceeds.
- **`README.md`** — the entry point for a new developer or evaluator: the pitch, install instructions (including optional extras), a before/after code example, and links to the docs above.
- **`CONTRIBUTING.md`** — how to set up a dev environment, run tests/lint/type-checks locally, the branch-per-milestone workflow from `PLAN.md §3`, and the PR expectations (tests required, one milestone per PR).
- **`CHANGELOG.md`** — a running log of released versions, following [Keep a Changelog](https://keepachangelog.com/) conventions and the Semantic Versioning policy from `PLAN.md §5`.
- **`LICENSE`** — the project's open-source license (MIT recommended per `PRD.md §7`).
- **`pyproject.toml`** — package metadata and dependencies; core has zero required dependencies, with `langchain` and `crewai` declared only as optional extras (`PRD.md §7`, `PLAN.md §6`). Also holds `ruff`/`mypy`/`pytest` configuration (`PLAN.md §5`).
- **`.pre-commit-config.yaml`** — runs `ruff` and `mypy` before each commit, mirroring the CI checks locally (`PLAN.md §5`).
- **`.gitignore`** — excludes `__pycache__/`, virtualenvs, `*.egg-info/`, `dist/`, `build/`, and `.pytest_cache/` from version control.

## `.github/workflows/`

- **`ci.yml`** — the CI pipeline described in `PLAN.md §5`: a core-only test/lint/type-check job, a separate bridge-test job that installs the `[langchain]`/`[crewai]` extras, and a dependency-isolation check. Runs on every pull request.

## `.cursor/rules/`

Persistent AI-agent guidance so implementation stays consistent with the architecture without re-explaining it every session. Rules are split by concern (always-apply vs. path-scoped globs) rather than one giant file:

| File | Scope | Purpose |
|---|---|---|
| `core.mdc` | always | Product identity, v1 non-negotiables, out-of-scope list |
| `architecture.mdc` | `adaptron/**/*.py` | Module boundaries, wrap order, adapter/pipeline rules |
| `dependencies.mdc` | always | Stdlib-only core; optional extras policy |
| `ai-workflow.mdc` | always | Code generation, scope discipline, git/commit habits |
| `python-standards.mdc` | `**/*.py` | Typing, docstrings, style, clarity |
| `error-handling.mdc` | `adaptron/**/*.py` | `AdaptronError` hierarchy and message requirements |
| `performance.mdc` | `adaptron/core/**/*.py` | Negligible overhead vs LLM calls |
| `bridges.mdc` | `adaptron/bridges/**/*.py` | Lazy imports, `can_wrap`/`adapt` contract |
| `testing.mdc` | `tests/**/*.py` | pytest layout, core vs bridge gating |
| `documentation.mdc` | `**/*.md` | Keep README/TASKS/PLAN synchronized with behavior |

## `adaptron/` — the core package

### `adaptron/__init__.py`

Public API surface only: `wrap`, `register_adapter`, `Pipeline`, `Agent`, plus
the post-v1 branching helper `parallel` (`PLAN.md §7`). Kept deliberately
small — anything not exported here isn't part of the supported interface.

### `adaptron/core/` — framework-agnostic pipeline engine

The heart of the system. Exists as a dedicated package, separate from `bridges/`, specifically so it can be imported and tested with zero optional dependencies installed. Each module maps directly to a concept in `PLAN.md §2`; see that document for the mechanism, not this one:

- **`agent.py`** — the `Agent` class.
- **`pipeline.py`** — the `Pipeline` class and the `>>` operator.
- **`adapters.py`** — the adapter registry.
- **`logging.py`** — stdlib-only verbose/silent execution logger.
- **`errors.py`** — the `AdaptronError` hierarchy. Present from Milestone 1 onward and extended incrementally, not introduced all at once (see `PLAN.md §3`, Milestones 1-3 and 7).

### `adaptron/bridges/` — optional, framework-specific adapters

Kept as separate, lazily-imported modules rather than folded into `core/` deliberately — this is what lets `pip install adaptron` stay dependency-free while `pip install adaptron[langchain]` opts in. Both are probed by `wrap()` *before* the plain-Python fallback (`PLAN.md §2.4`):

- **`langchain_bridge.py`** — duck-types LangChain agents/chains.
- **`crewai_bridge.py`** — duck-types CrewAI's agent/task interface.

## `examples/` — proof that the interoperability claim is real

Exists as runnable scripts rather than just README snippets so the interoperability claim is independently verifiable, not just described in prose (`PRD.md §5`, story 6):

- **`plain_python_pipeline.py`** — a minimal pipeline of wrapped plain-Python functions, no adapters required; the simplest possible "it works" example.
- **`cross_framework_pipeline.py`** — the flagship demo: one real LangChain agent, one real CrewAI agent, and one plain Python formatter, connected with `>>`, with at least one genuine type mismatch auto-resolved. This is the file the README's before/after comparison is drawn from.

## `docs/`

- **`demo-flagship.svg`** — an illustrative (not a live recording) animated stage diagram of the flagship cross-framework pipeline, embedded in the README for at-a-glance demo clarity (`PRD.md §3.2`).
- **`playground/`** — the stretch-goal interactive demo (Milestone 9): a simulated pipeline runner that replays the `cross_framework_pipeline.py` example visually (diagram + log output), explicitly labeled as illustrative rather than a live execution environment (`PRD.md §9` risk mitigation).

## `tests/` — automated test suite

One file per core module (`agent`, `pipeline`, `adapters`, `logging`, `errors`) plus one per bridge, plus e2e/post-v1 coverage, so a failure immediately localizes to the responsible module, mirroring the `core/`/`bridges/` split:

- **`test_agent.py`**, **`test_pipeline.py`**, **`test_adapters.py`**, **`test_logging.py`**, **`test_errors.py`** — run with zero optional dependencies installed.
- **`test_bridges_langchain.py`**, **`test_bridges_crewai.py`** — gated behind `pytest.importorskip(...)` so CI can run core tests without the extras, and bridge tests only when the relevant extra is installed (`PLAN.md §4`).
- **`test_examples.py`** — e2e coverage for both `examples/` scripts (Milestone 8); the plain-Python example runs with zero optional dependencies, the cross-framework example's mock-mode assertions are gated behind `pytest.importorskip("langchain")`/`("crewai")`.
- **`test_post_v1.py`** — coverage for the opt-in post-v1 backlog: best-effort mode, MRO adapter resolution, `parallel`, and `arun()` (`PLAN.md §7`).
