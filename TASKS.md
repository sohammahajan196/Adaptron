# Adaptron — Implementation Roadmap

**Status:** Not started — no product code exists yet (scaffolding docs and Cursor rules partly done).
**Related docs:** [PRD.md](./PRD.md) (what/why) · [PLAN.md](./PLAN.md) (architecture) · [STRUCTURE.md](./STRUCTURE.md) (layout) · [README.md](./README.md) (entry point)

---

## How to use this document

Work **top to bottom**. Each phase is a meaningful milestone (`PLAN.md` §3). Each task is sized for roughly **one Cursor chat / one focused coding session**. Check boxes as you go.

| Label | Meaning |
|---|---|
| **Prerequisites** | Must be true before starting the phase/task |
| **Core** | Primary implementation work |
| **Testing** | Validation required before moving on |
| **Documentation** | Docs/changelog updates for the change |
| **Optional** | Stretch / nice-to-have within the same scope (not new features) |

`PLAN.md` stays the stable architecture reference. This file is the live execution tracker and will change constantly.

### Phase dependency overview

```
Phase 0  →  Phase 1  →  Phase 2  →  Phase 3  →  Phase 4
                                                      ↓
                              Phase 5 (LangChain) → Phase 6 (CrewAI)
                                                      ↓
                                                  Phase 7
                                                      ↓
                                                  Phase 8
                                                      ↓
                                          Phase 9 (Optional stretch)

Post-v1 backlog: do not start until Phase 8 has shipped.
```

**Independent within a phase:** testing and documentation tasks run *after* their matching core task, never before. Phases 5 and 6 both need Phase 4 complete; Phase 6’s `wrap()` wiring assumes Phase 5’s probe order is already in place.

---

# Phase 0: Repository Scaffolding

## Objective

Create an installable, lintable, CI-ready empty package so later phases have a real home. No product behavior yet.

## Deliverables

- `pyproject.toml` with zero required deps and optional extras stubs
- Package skeleton (`adaptron/`, `tests/`)
- Lint/format/type-check tooling + pre-commit
- CI workflow (core / bridges / dependency isolation)
- `LICENSE`, `CHANGELOG.md`, `.gitignore`
- Confirmed local/CI green on empty tree

## Prerequisites

- None (start here)
- Cursor rules and `CONTRIBUTING.md` already exist (do not recreate from scratch)

## Tasks

### Task 0.1 — Project metadata and ignore rules
**Type:** Core  
**Goal:** Package identity and VCS hygiene exist.  
**Description:** Create root packaging and ignore files matching `STRUCTURE.md` / `PLAN.md` §5–6.  
**Files Expected to Change:** `pyproject.toml`, `.gitignore`, `LICENSE`, `CHANGELOG.md`  
**Dependencies:** None  
**Acceptance Criteria:** `pip install -e .` works (empty package); MIT license present; `CHANGELOG.md` has `[Unreleased]`; ignore list covers `__pycache__/`, `*.egg-info/`, `dist/`, `build/`, `.pytest_cache/`, `.mypy_cache/`, `.venv/`.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Create `pyproject.toml`: name `adaptron`, `requires-python >= 3.10`, **zero** required dependencies
- [x] Stub `[project.optional-dependencies]` for `langchain` and `crewai` (pins filled/refined in Phases 5–6)
- [x] Add `dev` optional extra stub for `pytest`, `ruff`, `mypy` (versions chosen at scaffolding time)
- [x] Add `.gitignore` with the paths above
- [x] Add `LICENSE` (MIT — `PRD.md` §7)
- [x] Create `CHANGELOG.md` with an `[Unreleased]` section
- [x] *(Documentation)* No README rewrite required beyond confirming install instructions still match

### Task 0.2 — Package skeleton
**Type:** Core  
**Goal:** Importable empty package matching `STRUCTURE.md`.  
**Description:** Create namespace packages only — no modules yet beyond `__init__.py`.  
**Files Expected to Change:** `adaptron/__init__.py`, `adaptron/core/__init__.py`, `adaptron/bridges/__init__.py`, `tests/__init__.py`  
**Dependencies:** Task 0.1  
**Acceptance Criteria:** `import adaptron` succeeds; `adaptron.core` and `adaptron.bridges` import without error; no third-party imports.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Create `adaptron/__init__.py` (empty public API for now; version optional)
- [x] Create `adaptron/core/__init__.py`
- [x] Create `adaptron/bridges/__init__.py`
- [x] Create `tests/__init__.py`
- [x] *(Testing)* Smoke: `python -c "import adaptron"` in a clean venv after `pip install -e .`

### Task 0.3 — Tooling configuration
**Type:** Core  
**Goal:** Ruff + mypy configured and runnable locally.  
**Description:** Configure tooling in `pyproject.toml` and pre-commit hooks per `PLAN.md` §5.  
**Files Expected to Change:** `pyproject.toml`, `.pre-commit-config.yaml`  
**Dependencies:** Task 0.1  
**Acceptance Criteria:** `ruff check .`, `ruff format --check .`, and `mypy adaptron` (or `adaptron/core` when populated) exit 0 on the empty tree.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Add `[tool.ruff]` / format settings to `pyproject.toml`
- [x] Add `[tool.mypy]` (strict enough for core; document bridge looseness later)
- [x] Add `[tool.pytest.ini_options]` basics (`testpaths = ["tests"]`)
- [x] Create `.pre-commit-config.yaml` running `ruff check`, `ruff format --check`, `mypy`
- [x] *(Testing)* Run ruff and mypy locally on the empty package
- [x] *(Documentation)* Ensure `CONTRIBUTING.md` commands still match (edit only if paths/commands differ)

### Task 0.4 — CI workflow
**Type:** Core + Testing  
**Goal:** GitHub Actions runs core checks, bridge job stub, and dependency-isolation check.  
**Description:** Implement `.github/workflows/ci.yml` per `PLAN.md` §5 (matrix Python 3.10–3.12).  
**Files Expected to Change:** `.github/workflows/ci.yml`  
**Dependencies:** Tasks 0.1–0.3  
**Acceptance Criteria:** Workflow runs on PR; core job installs bare package + pytest/ruff/mypy; isolation job asserts `langchain`/`crewai` absent after bare install; bridge job can be empty/`continue` until Phases 5–6 (or runs empty suite).  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Create `.github/workflows/ci.yml` with core-tests job (no extras)
- [x] Add bridge-tests job that installs `[langchain,crewai]` (suite may be empty until Phase 5–6)
- [x] Add dependency-isolation job verifying extras are not present on bare install
- [x] *(Testing)* Push/PR or `act`/manual dispatch and confirm jobs start (green on empty tree)
- [x] *(Documentation)* Link CI status expectations from `CONTRIBUTING.md` if missing

### Task 0.5 — Phase 0 close-out
**Type:** Documentation + Testing  
**Goal:** Scaffolding is verified and recorded.  
**Description:** Confirm Cursor rules already present; mark checklist; small changelog note.  
**Files Expected to Change:** `CHANGELOG.md`, this file  
**Dependencies:** Tasks 0.1–0.4  
**Acceptance Criteria:** Rules under `.cursor/rules/` remain in place; CONTRIBUTING already written; Unreleased mentions scaffolding.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Cursor rules under `.cursor/rules/*.mdc` present (do not regenerate wholesale)
- [x] `CONTRIBUTING.md` present
- [x] *(Documentation)* Note scaffolding under `[Unreleased]` in `CHANGELOG.md`
- [x] *(Testing)* Final local: install, import, ruff, mypy, pytest (0 tests OK)

## Phase Completion Checklist
- [x] All tasks completed
- [x] Tests / lint / type-check passing (empty suite OK)
- [x] Documentation updated (`CHANGELOG`, CONTRIBUTING aligned)
- [x] Ready for next phase

---

# Phase 1: Core Agent & Port Abstraction

## Objective

Introduce `Agent`, type inference, `WrapError`, and plain-Python `wrap()` — no pipelines yet.

## Deliverables

- `adaptron.core.errors` with `AdaptronError`, `WrapError`
- `adaptron.core.agent.Agent`
- `wrap()` for callables / `__call__` instances only
- `tests/test_agent.py` green with zero optional deps
- Public exports: `wrap`, `Agent`

## Prerequisites

- Phase 0 complete

## Tasks

### Task 1.1 — Exception base + WrapError
**Type:** Core  
**Goal:** Shared error base exists for wrap failures.  
**Description:** Implement hierarchy start per `PLAN.md` Milestone 1.  
**Files Expected to Change:** `adaptron/core/errors.py`, `adaptron/core/__init__.py` (optional re-exports)  
**Dependencies:** Phase 0  
**Acceptance Criteria:** `WrapError` subclasses `AdaptronError`; raising it with a message works; no third-party imports.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Implement `AdaptronError(Exception)`
- [x] Implement `WrapError(AdaptronError)` with actionable message contract in docstring
- [x] *(Testing)* Minimal smoke import in a throwaway assert or defer to Task 1.4
- [x] *(Documentation)* Docstrings only (no README change yet)

### Task 1.2 — Agent class + type inference
**Type:** Core  
**Goal:** Wrap a callable with name and I/O types.  
**Description:** Types priority: explicit args → `typing.get_type_hints` → `Any` (`PLAN.md` §2.1).  
**Files Expected to Change:** `adaptron/core/agent.py`  
**Dependencies:** Task 1.1  
**Acceptance Criteria:** `Agent` exposes `.input_type`, `.output_type`, `.name`, `.__call__`; calling delegates to wrapped callable; single value in / single value out.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Implement `Agent` storing callable + types + name
- [x] Implement type resolution helper (`inspect.signature` + `get_type_hints`)
- [x] Support explicit type overrides for input/output
- [x] Fall back to `typing.Any` when hints missing
- [x] Google-style docstring on `Agent`
- [x] *(Testing)* Covered in Task 1.4

### Task 1.3 — Plain-Python `wrap()`
**Type:** Core  
**Goal:** Public `wrap()` creates `Agent` or raises `WrapError`.  
**Description:** Callable functions and `__call__` instances only; no bridges (`PLAN.md` §2.4 catch-all path only).  
**Files Expected to Change:** `adaptron/__init__.py` (or thin `wrap` module re-exported here)  
**Dependencies:** Task 1.2  
**Acceptance Criteria:** Valid callables wrap; non-callable raises `WrapError` naming what failed; exports `wrap` and `Agent`.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Implement `wrap(obj, *, input_type=..., output_type=..., name=...)` as designed
- [x] Detect functions and callable instances; reject unusable objects with `WrapError`
- [x] Export `wrap`, `Agent` from `adaptron/__init__.py`
- [x] Do **not** probe LangChain/CrewAI yet
- [x] *(Documentation)* Module docstring stating bridges come later

### Task 1.4 — Agent / wrap tests
**Type:** Testing  
**Goal:** Core wrap behavior verified without optional deps.  
**Description:** `tests/test_agent.py` cases from `PLAN.md` / prior checklist.  
**Files Expected to Change:** `tests/test_agent.py`  
**Dependencies:** Task 1.3  
**Acceptance Criteria:** Typed fn, untyped fn → `Any`, callable class, wrap failure all covered and pass under bare `pip install -e .`.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Test typed function inference
- [x] Test untyped function → `Any`
- [x] Test class with `__call__`
- [x] Test `WrapError` on non-wrappable object (message actionable)
- [x] Test explicit type override wins over hints
- [x] Run `pytest tests/test_agent.py`

### Task 1.5 — Phase 1 documentation
**Type:** Documentation  
**Goal:** Changelog reflects Agent/`wrap`.  
**Files Expected to Change:** `CHANGELOG.md`, optionally brief note in `README.md` status if desired  
**Dependencies:** Task 1.4  
**Acceptance Criteria:** Unreleased notes Agent + wrap (plain Python).  
**Estimated Complexity:** Low

#### Subtasks
- [x] Update `CHANGELOG.md` under `[Unreleased]`
- [x] Tick this phase’s boxes in `TASKS.md`

## Phase Completion Checklist
- [x] All tasks completed
- [x] Tests passing (`test_agent.py`)
- [x] Documentation updated
- [x] Ready for next phase

---

# Phase 2: Pipeline & `>>` Operator

## Objective

Linear, composable pipelines of Agents with sync `run()`, flattening, and `PipelineExecutionError` — adapters still stubbed/passthrough.

## Deliverables

- `Pipeline` class with flatten + composability
- `>>` on `Agent` and `Pipeline`
- `run()` threading outputs
- `PipelineExecutionError`
- `tests/test_pipeline.py` green
- Export `Pipeline`

## Prerequisites

- Phase 1 complete

## Tasks

### Task 2.1 — PipelineExecutionError
**Type:** Core  
**Goal:** Runtime stage failures have a typed error.  
**Files Expected to Change:** `adaptron/core/errors.py`  
**Dependencies:** Phase 1  
**Acceptance Criteria:** Error can carry stage name and input context; subclasses `AdaptronError`.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Add `PipelineExecutionError` with fields/message for stage + input preview
- [x] Docstring documents when it is raised
- [x] *(Testing)* Deferred to Task 2.4

### Task 2.2 — Pipeline structure + `>>` flattening
**Type:** Core  
**Goal:** Chaining builds one flat pipeline.  
**Description:** Implement stage list, `__rshift__`/`__rrshift__`, flatten nested pipelines (`PLAN.md` §2.2). Adapter resolution still no-op / always compatible.  
**Files Expected to Change:** `adaptron/core/pipeline.py`, `adaptron/core/agent.py`  
**Dependencies:** Task 2.1  
**Acceptance Criteria:** `a >> b >> c` is one `Pipeline` with three stages; `(a >> b) >> c` identical flatten; `.input_type`/`.output_type` from first/last stage.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Implement `Pipeline` storing ordered stages
- [x] Implement `Agent.__rshift__` / `__rrshift__`
- [x] Implement `Pipeline.__rshift__` (and left-side if needed) for composability
- [x] Flatten so chains never nest Pipeline-in-Pipeline as stages
- [x] Expose `.input_type` / `.output_type`
- [x] Stub compatibility check (always pass) pending Phase 3

### Task 2.3 — `Pipeline.run()` + export
**Type:** Core  
**Goal:** Execute stages in order; wrap failures.  
**Files Expected to Change:** `adaptron/core/pipeline.py`, `adaptron/__init__.py`  
**Dependencies:** Task 2.2  
**Acceptance Criteria:** Output of stage N is input of N+1; stage exception → `PipelineExecutionError` with stage identity; `Pipeline` exported.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Implement `run(input)` loop
- [x] Catch stage exceptions → `PipelineExecutionError`
- [x] Export `Pipeline` from `adaptron/__init__.py`
- [x] Silent logging default (verbose arrives Phase 4)

### Task 2.4 — Pipeline tests
**Type:** Testing  
**Goal:** Composition and failure paths verified.  
**Files Expected to Change:** `tests/test_pipeline.py`  
**Dependencies:** Task 2.3  
**Acceptance Criteria:** 2-stage, 3-stage, flatten, nested composition, failing stage all pass.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Test 2-stage and 3-stage correct output
- [x] Assert `a >> b >> c` is single Pipeline, not nested
- [x] Assert `(a >> b) >> c` equals flatten of three agents
- [x] Assert mid-pipeline failure raises `PipelineExecutionError` with stage context
- [x] Run `pytest tests/test_pipeline.py tests/test_agent.py`

### Task 2.5 — Phase 2 documentation
**Type:** Documentation  
**Dependencies:** Task 2.4  
**Acceptance Criteria:** Changelog mentions `>>` and `Pipeline`.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Update `CHANGELOG.md`
- [x] Optionally add one-line usage snippet comment in `pipeline.py` module docstring

## Phase Completion Checklist
- [x] All tasks completed
- [x] Tests passing
- [x] Documentation updated
- [x] Ready for next phase

---

# Phase 3: Adapter Registry & Auto-Adaptation

## Objective

Exact-pair adapter registry, construction-time insertion or `NoAdapterError`, default adapters, and `register_adapter` public API.

## Deliverables

- `adaptron/core/adapters.py` registry
- `NoAdapterError`
- Pipeline construction resolves / inserts adapters
- Default `str → dict` (+ demo `Message` / `str → Message`)
- `tests/test_adapters.py` green
- Export `register_adapter`

## Prerequisites

- Phase 2 complete

## Tasks

### Task 3.1 — NoAdapterError
**Type:** Core  
**Goal:** Construction-time mismatch error type exists.  
**Files Expected to Change:** `adaptron/core/errors.py`  
**Dependencies:** Phase 2  
**Acceptance Criteria:** Message includes both types and suggests `register_adapter(Source, Target, fn)`.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Implement `NoAdapterError` with source/target type context
- [x] Docstring + example suggested fix string format
- [x] *(Testing)* Deferred to Task 3.4

### Task 3.2 — Registry + register_adapter
**Type:** Core  
**Goal:** Exact `(type, type)` map with overwrite warning.  
**Files Expected to Change:** `adaptron/core/adapters.py`  
**Dependencies:** Task 3.1  
**Acceptance Criteria:** Register/lookup O(1); re-register warns (stdlib `warnings` or logger); no MRO matching.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Implement registry `dict[tuple[type, type], Callable]`
- [x] Implement `register_adapter(source, target, fn)`
- [x] Warn on overwrite (not silent)
- [x] Lookup helper used by Pipeline (`resolve` / `get_adapter`)
- [x] Export `register_adapter` from `adaptron/__init__.py`

### Task 3.3 — Construction-time resolution in Pipeline
**Type:** Core  
**Goal:** On `>>`, insert adapter or raise; `Any` skips.  
**Files Expected to Change:** `adaptron/core/pipeline.py`  
**Dependencies:** Task 3.2  
**Acceptance Criteria:** Exact type match → no adapter; registered pair → adapter stage inserted; `Any` either side → skip; else `NoAdapterError` at construction, never at `run()`.  
**Estimated Complexity:** High

#### Subtasks
- [x] Replace Phase 2 stub with real resolution between adjacent stages
- [x] Insert adapter as its own stage (named for logging later)
- [x] Skip when input or output type is `Any`
- [x] Raise `NoAdapterError` immediately when unresolved
- [x] Preserve flatten/composability behavior from Phase 2

### Task 3.4 — Default adapters
**Type:** Core  
**Goal:** Small useful defaults for demos/docs.  
**Files Expected to Change:** `adaptron/core/adapters.py` (or `adaptron/core/defaults.py` imported at package init — keep core stdlib-only)  
**Dependencies:** Task 3.2  
**Acceptance Criteria:** `str → dict` wraps as `{"text": ...}`; example `Message` + `str → Message` available for docs.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Register default `str → dict`
- [x] Add demo `Message` type + `str → Message` adapter (docs/demo)
- [x] Ensure defaults load without user action when package imported (or document explicit import — pick one and stick to README later)

### Task 3.5 — Adapter tests
**Type:** Testing  
**Files Expected to Change:** `tests/test_adapters.py`  
**Dependencies:** Tasks 3.3–3.4  
**Acceptance Criteria:** Auto-insert, construction `NoAdapterError`, re-register warning, `Any` skip covered.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Test registered mismatch auto-inserts and `run()` succeeds
- [x] Test unregistered mismatch raises at `a >> b`, not at `run()`
- [x] Test re-registration emits warning
- [x] Test `Any` skips resolution
- [x] Run full core suite

### Task 3.6 — Phase 3 documentation
**Type:** Documentation  
**Dependencies:** Task 3.5  
**Acceptance Criteria:** Changelog documents `register_adapter` and construction-time checks; note exact-pair v1 limitation.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Update `CHANGELOG.md`
- [x] Ensure error message text matches docs suggestion

## Phase Completion Checklist
- [x] All tasks completed
- [x] Tests passing
- [x] Documentation updated
- [x] Ready for next phase

---

# Phase 4: Logging & Observability

## Objective

Stdlib logging of every agent/adapter stage, toggled by `verbose`, silent by default.

## Deliverables

- `adaptron/core/logging.py`
- `Pipeline.run(..., verbose=False|True)`
- Caplog-based tests
- Changelog update

## Prerequisites

- Phase 3 complete (adapters must appear as stages in logs)

## Tasks

### Task 4.1 — Logger helper
**Type:** Core  
**Goal:** Dedicated `adaptron` logger namespace, stdlib only.  
**Files Expected to Change:** `adaptron/core/logging.py`  
**Dependencies:** Phase 3  
**Acceptance Criteria:** Helper can emit one-line stage records; truncation of previews; no third-party deps.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Create logger named `adaptron` (or `adaptron.pipeline`)
- [x] Implement stage log formatter: name, in-type, out-type, truncated preview
- [x] Unit-testable pure helpers for truncation if non-trivial

### Task 4.2 — Wire verbose into `run()`
**Type:** Core  
**Goal:** Opt-in per-run verbosity.  
**Files Expected to Change:** `adaptron/core/pipeline.py`  
**Dependencies:** Task 4.1  
**Acceptance Criteria:** Default silent; `verbose=True` logs agents and adapters in order; no behavior change to outputs.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Add `verbose: bool = False` to `run`
- [x] Log each stage including inserted adapters
- [x] Keep default quiet (no handler noise unless user configured logging)

### Task 4.3 — Logging tests
**Type:** Testing  
**Files Expected to Change:** `tests/test_pipeline.py` or `tests/test_logging.py`  
**Dependencies:** Task 4.2  
**Acceptance Criteria:** `caplog` shows stage names/types in order for a multi-stage adapted pipeline.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Capture logs with `caplog` / logger level INFO
- [x] Assert order includes adapter stage when adaptation occurred
- [x] Assert silent path produces no adaptron stage logs (or only when verbose)

### Task 4.4 — Phase 4 documentation
**Type:** Documentation  
**Dependencies:** Task 4.3  
**Acceptance Criteria:** Changelog + optional README mention of `verbose=True`.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Update `CHANGELOG.md`
- [x] *(Optional)* Add log sample to README only if README already describes verbose (keep in sync)

## Phase Completion Checklist
- [x] All tasks completed
- [x] Tests passing
- [x] Documentation updated
- [x] Ready for next phase

---

# Phase 5: LangChain Bridge

## Objective

Optional, duck-typed LangChain bridge probed **before** plain-Python fallback; lazy imports; gated tests.

## Deliverables

- `adaptron/bridges/langchain_bridge.py` (`can_wrap`, `adapt`)
- `wrap()` probe order: LangChain → (CrewAI later) → plain Python
- `pyproject.toml` langchain extra pin
- `tests/test_bridges_langchain.py` with `importorskip`
- Regression: LangChain object not mis-wrapped as plain Python

## Prerequisites

- Phase 4 complete
- Confirm current stable LangChain major range before pinning (`PLAN.md` §6)

## Tasks

### Task 5.1 — LangChain extra pin
**Type:** Core  
**Goal:** Documented optional dependency.  
**Files Expected to Change:** `pyproject.toml`  
**Dependencies:** Phase 4  
**Acceptance Criteria:** `pip install adaptron[langchain]` installs pinned range; bare install still has no langchain.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Research current stable LangChain version; set pin
- [x] Update optional-dependencies in `pyproject.toml`
- [x] *(Testing)* Isolation check still passes on bare install

### Task 5.2 — Bridge module
**Type:** Core  
**Goal:** `can_wrap` / `adapt` for LangChain invoke/run.  
**Files Expected to Change:** `adaptron/bridges/langchain_bridge.py`  
**Dependencies:** Task 5.1  
**Acceptance Criteria:** Duck-type `.invoke`/`.run`; `adapt` returns `Agent` defaulting `str → str`; lazy import; `WrapError` if unusable.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Implement `can_wrap(obj) -> bool`
- [x] Implement `adapt(obj) -> Agent` with lazy langchain import
- [x] Default types `str → str` unless overridden
- [x] Module must not pollute `core/` with langchain imports

### Task 5.3 — Wire into `wrap()`
**Type:** Core  
**Goal:** Correct probe order.  
**Files Expected to Change:** `adaptron/__init__.py` (wrap dispatcher)  
**Dependencies:** Task 5.2  
**Acceptance Criteria:** LangChain objects hit bridge; plain callables still wrap; bridge skipped if not installed.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Probe LangChain bridge first when available
- [x] Fall back to plain-Python wrap
- [x] Leave placeholder comment for CrewAI slot (Phase 6)

### Task 5.4 — LangChain bridge tests
**Type:** Testing  
**Files Expected to Change:** `tests/test_bridges_langchain.py`  
**Dependencies:** Task 5.3  
**Acceptance Criteria:** Skips without langchain; with langchain, wrap uses bridge; regression vs plain-Python fallback.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Gate file with `pytest.importorskip("langchain")`
- [x] Test adapt/delegate behavior with a minimal fake or light LC object
- [x] Regression: object matching LC duck-types is not wrapped as bare callable
- [x] CI bridge job runs this file

### Task 5.5 — Phase 5 documentation
**Type:** Documentation  
**Dependencies:** Task 5.4  
**Acceptance Criteria:** Changelog + install note for `[langchain]`.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Update `CHANGELOG.md`
- [x] Confirm README install extras still accurate (edit if pins/docs disagree)

## Phase Completion Checklist
- [x] All tasks completed
- [x] Tests passing (core + langchain when installed)
- [x] Documentation updated
- [x] Ready for next phase

---

# Phase 6: CrewAI Bridge

## Objective

Same bridge pattern for CrewAI; probe **after** LangChain and **before** plain-Python.

## Deliverables

- `adaptron/bridges/crewai_bridge.py`
- Updated `wrap()` order: LangChain → CrewAI → plain Python
- CrewAI extra pin
- `tests/test_bridges_crewai.py`

## Prerequisites

- Phase 5 complete (probe order / dispatcher shape)

**Note:** Implementing the CrewAI module file can be drafted in parallel with Phase 5 mentally, but **do not merge `wrap()` CrewAI wiring** until Phase 5’s LangChain-first order exists.

## Tasks

### Task 6.1 — CrewAI extra pin
**Type:** Core  
**Files Expected to Change:** `pyproject.toml`  
**Dependencies:** Phase 5  
**Acceptance Criteria:** `[crewai]` extra pinned; bare install isolation unchanged.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Confirm current stable CrewAI range; pin in `pyproject.toml`
- [x] *(Testing)* Bare install isolation job still green

### Task 6.2 — Bridge module
**Type:** Core  
**Files Expected to Change:** `adaptron/bridges/crewai_bridge.py`  
**Dependencies:** Task 6.1  
**Acceptance Criteria:** `can_wrap` / `adapt` for CrewAI agent/task interface; lazy import; defaults appropriate (`str→str` or documented).  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Implement duck-typed `can_wrap`
- [x] Implement `adapt` → `Agent`
- [x] Fail loudly with `WrapError` on unsupported shapes

### Task 6.3 — Wire into `wrap()`
**Type:** Core  
**Files Expected to Change:** `adaptron/__init__.py`  
**Dependencies:** Task 6.2 + Phase 5 wrap order  
**Acceptance Criteria:** Order is LangChain → CrewAI → plain Python; first match wins.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Insert CrewAI probe after LangChain
- [x] Keep plain-Python last
- [x] *(Testing)* Covered in Task 6.4

### Task 6.4 — CrewAI bridge tests
**Type:** Testing  
**Files Expected to Change:** `tests/test_bridges_crewai.py`  
**Dependencies:** Task 6.3  
**Acceptance Criteria:** `importorskip("crewai")`; wrap path verified; no false plain-Python wrap.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Gate with `pytest.importorskip("crewai")`
- [x] Adapt/delegate test with minimal stub or light CrewAI object
- [x] Regression vs plain-Python fallback
- [x] CI bridge job includes this file

### Task 6.5 — Phase 6 documentation
**Type:** Documentation  
**Dependencies:** Task 6.4  
**Acceptance Criteria:** Changelog + README extras for `[crewai]` / `[langchain,crewai]`.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Update `CHANGELOG.md`
- [x] Sync README install section if needed

## Phase Completion Checklist
- [x] All tasks completed
- [x] Tests passing
- [x] Documentation updated
- [x] Ready for next phase

---

# Phase 7: Error Handling Audit

## Objective

Consistency pass over all exceptions — not new product features. Adapter conversion failures wrapped cleanly; messages actionable without reading source.

## Deliverables

- Audited error sites (wrap, construction, run, adapter failures)
- `tests/test_errors.py` asserting message content
- Changelog note

## Prerequisites

- Phase 6 complete (all error paths exist)

## Tasks

### Task 7.1 — Codebase error audit
**Type:** Core  
**Goal:** Every raise site meets `PRD.md` §6.6 / §7 Debuggability.  
**Files Expected to Change:** `adaptron/core/*.py`, possibly bridges  
**Dependencies:** Phase 6  
**Acceptance Criteria:** Checklist of raise sites reviewed; each names stage/types/input as applicable.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Inventory all `raise` sites under `adaptron/`
- [x] Fix any message that is not actionable standalone
- [x] Ensure adapter fn exceptions become `AdaptronError` subclass (e.g. extend `PipelineExecutionError` or dedicated conversion error under existing hierarchy — do not invent parallel trees)

### Task 7.2 — Adapter failure wrapping
**Type:** Core  
**Goal:** Mid-conversion failures never pass bad data or raw opaque traces only.  
**Files Expected to Change:** `adaptron/core/pipeline.py` and/or `adapters.py`  
**Dependencies:** Task 7.1  
**Acceptance Criteria:** Deliberate failing adapter in a test becomes wrapping `AdaptronError` with context.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Catch adapter callable exceptions during `run()`
- [x] Re-raise as project error with stage/types/input
- [x] Do not continue pipeline after adapter failure

### Task 7.3 — Error message tests
**Type:** Testing  
**Files Expected to Change:** `tests/test_errors.py`  
**Dependencies:** Task 7.2  
**Acceptance Criteria:** Asserts on message content for `WrapError`, `NoAdapterError`, `PipelineExecutionError`, adapter-failure wrap.  
**Estimated Complexity:** Medium

#### Subtasks
- [x] Message tests for each exception type
- [x] Adapter mid-conversion failure test
- [x] Run full suite

### Task 7.4 — Phase 7 documentation
**Type:** Documentation  
**Dependencies:** Task 7.3  
**Acceptance Criteria:** Changelog notes error polish; CONTRIBUTING “actionable errors” still accurate.  
**Estimated Complexity:** Low

#### Subtasks
- [x] Update `CHANGELOG.md`
- [x] Spot-check CONTRIBUTING error guidance

## Phase Completion Checklist
- [x] All tasks completed
- [x] Tests passing
- [x] Documentation updated
- [x] Ready for next phase

---

# Phase 8: Examples, README Proof & Release Hygiene

## Objective

Prove interoperability with runnable examples and finalize the human-facing README story; consider `v0.1.0`.

## Deliverables

- `examples/plain_python_pipeline.py`
- `examples/cross_framework_pipeline.py` (real LangChain + CrewAI + plain Python + ≥1 auto-adapt)
- E2E tests / assertions for examples
- README fully accurate vs shipped API
- Optional GIF/recording
- Changelog; optional tag `v0.1.0`

## Prerequisites

- Phase 7 complete

## Tasks

### Task 8.1 — Plain-Python example
**Type:** Core  
**Goal:** Minimal “it works” script, no framework extras required.  
**Files Expected to Change:** `examples/plain_python_pipeline.py`  
**Dependencies:** Phase 7  
**Acceptance Criteria:** Runnable with bare `adaptron`; demonstrates `wrap` + `>>` (+ adapter if useful).  
**Estimated Complexity:** Low

#### Subtasks
- [ ] Write script matching README quickstart spirit
- [ ] *(Testing)* Manual run + optional thin test importing the pipeline logic
- [ ] *(Documentation)* README points at this file

### Task 8.2 — Cross-framework example
**Type:** Core  
**Goal:** Flagship demo with genuine type mismatch auto-resolved.  
**Files Expected to Change:** `examples/cross_framework_pipeline.py`  
**Dependencies:** Task 8.1, Phases 5–6  
**Acceptance Criteria:** One LC agent, one CrewAI agent, one plain formatter; ≥1 adapter used; needs extras + API keys as documented.  
**Estimated Complexity:** High

#### Subtasks
- [ ] Implement real (or well-documented mockable) cross-framework pipeline
- [ ] Show auto-adaptation in verbose logs
- [ ] Document env vars / keys at top of file
- [ ] Label clearly if any part is mocked for CI

### Task 8.3 — Example / e2e tests
**Type:** Testing  
**Files Expected to Change:** `tests/` (e.g. `test_examples.py` or markers)  
**Dependencies:** Tasks 8.1–8.2  
**Acceptance Criteria:** Plain example tested without extras; cross-framework gated or uses mocks; assert adapter involved via logs when applicable.  
**Estimated Complexity:** Medium

#### Subtasks
- [ ] Test plain example output
- [ ] Gate or mock cross-framework so CI can pass without paid APIs where possible
- [ ] Assert ≥1 adapter stage when testing adaptation claim

### Task 8.4 — README accuracy pass
**Type:** Documentation  
**Goal:** README matches shipped API (already drafted — verify, don’t invent features).  
**Files Expected to Change:** `README.md`  
**Dependencies:** Task 8.3  
**Acceptance Criteria:** Before/after, install, quickstart, links, status/roadmap accurate; examples paths correct.  
**Estimated Complexity:** Medium

#### Subtasks
- [ ] Verify every code sample against current API
- [ ] Update status/roadmap checkboxes vs completed phases
- [ ] Link examples directory

### Task 8.5 — Demo asset + release notes
**Type:** Documentation / Optional  
**Goal:** Portfolio clarity + version hygiene.  
**Files Expected to Change:** `README.md`, `CHANGELOG.md`, git tag (when releasing)  
**Dependencies:** Task 8.4  
**Acceptance Criteria:** Changelog ready for `0.1.0`; GIF optional but recommended (`PRD.md` §3.2).  
**Estimated Complexity:** Medium

#### Subtasks
- [ ] *(Optional)* Record terminal GIF/video of flagship example
- [ ] Finalize `CHANGELOG.md` for `0.1.0`
- [ ] *(Optional)* Tag `v0.1.0` when ready to release

## Phase Completion Checklist
- [ ] All **required** tasks completed (8.5 GIF is Optional)
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Ready for Phase 9 (stretch) or pause at v0.1

---

# Phase 9: Interactive Playground (Optional Stretch)

## Objective

Illustrative, non-live replay of the flagship pipeline for docs (`PRD.md` §11 item 9 / §9 risk). **Not required for v1 core library.**

## Deliverables

- Content under `docs/playground/`
- Explicit “simulated / illustrative” labeling
- Link from README

## Prerequisites

- Phase 8 complete (flagship example exists to replay)

## Tasks

### Task 9.1 — Choose format
**Type:** Core (planning)  
**Goal:** Pick static site vs notebook; document choice in `docs/playground/README.md`.  
**Files Expected to Change:** `docs/playground/README.md`  
**Dependencies:** Phase 8  
**Acceptance Criteria:** Format decided and written down; no live LLM dependency.  
**Estimated Complexity:** Low

#### Subtasks
- [ ] Decide static site vs notebook
- [ ] Document decision and “illustrative only” banner requirements

### Task 9.2 — Build mocked replay
**Type:** Core  
**Goal:** Visual + log replay of Phase 8 flagship.  
**Files Expected to Change:** `docs/playground/**`  
**Dependencies:** Task 9.1  
**Acceptance Criteria:** Shows stages/adapters/result; clearly simulated.  
**Estimated Complexity:** High

#### Subtasks
- [ ] Script mocked stage outputs
- [ ] Render diagram or sequential log UI
- [ ] Banner: not live execution

### Task 9.3 — Link from README
**Type:** Documentation  
**Files Expected to Change:** `README.md`, `CHANGELOG.md`  
**Dependencies:** Task 9.2  
**Acceptance Criteria:** README links playground; notes illustrative.  
**Estimated Complexity:** Low

#### Subtasks
- [ ] Add README section/link
- [ ] Changelog stretch note

## Phase Completion Checklist
- [ ] All tasks completed (or phase explicitly deferred)
- [ ] Tests N/A or light smoke if applicable
- [ ] Documentation updated
- [ ] Ready for post-v1 backlog only when product API is stable

---

# Post-v1 Backlog (Not Scheduled)

Tracks [PRD.md §12](./PRD.md) / [PLAN.md §7](./PLAN.md). **Do not start until Phase 8 has shipped** and real usage exists. These are **not** Phase 0–9 tasks and must not block v1.

| Item | Type | Notes |
|---|---|---|
| Best-effort mode (`Pipeline(strict=False)` or equivalent) | Optional enhancement | Construction still fails by default |
| Subclass / MRO-aware adapter resolution | Optional enhancement | Replaces exact-pair-only if needed |
| Many-to-one adapter coercion | Optional enhancement | |
| Branching / parallel pipeline topology | Optional enhancement | Still linear-only in v1 |
| Native async (`arun()`) | Optional enhancement | Sync-only in v1 |

- [ ] Best-effort mode
- [ ] Subclass/MRO-aware adapter resolution
- [ ] Many-to-one adapter coercion
- [ ] Branching/parallel pipelines
- [ ] Native async execution

---

## Quick reference: session sizing

Prefer starting a new Cursor chat per **Task X.Y** (not an entire phase). Within a task, finish **Core → Testing → Documentation** before opening the next task.
