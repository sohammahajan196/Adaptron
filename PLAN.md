# Adaptron — Technical Plan

**Status:** Draft
**Related docs:** [PRD.md](./PRD.md) — product requirements this plan implements · [STRUCTURE.md](./STRUCTURE.md) — full repo layout and file-by-file rationale · [TASKS.md](./TASKS.md) — granular execution checklist for these milestones

---

## 1. Repository structure

This is the shape of the package and its milestone-relevant files; see [STRUCTURE.md](./STRUCTURE.md) for the complete tree (including tooling, CI, and OSS housekeeping files) and the rationale behind each one.

```
adaptron/
├── adaptron/                    # core package
│   ├── __init__.py               # public API: wrap, register_adapter, Pipeline, Agent
│   ├── core/
│   │   ├── agent.py               # Agent class, port declaration/inference
│   │   ├── pipeline.py            # Pipeline, >> operator, construction-time checks
│   │   ├── adapters.py            # adapter registry
│   │   ├── logging.py             # verbose/silent execution logger
│   │   └── errors.py              # AdaptronError hierarchy (grows incrementally — see §3)
│   └── bridges/
│       ├── langchain_bridge.py    # optional, lazy-imported
│       └── crewai_bridge.py       # optional, lazy-imported
├── examples/
│   ├── plain_python_pipeline.py
│   └── cross_framework_pipeline.py
├── tests/                        # one test file per core module + bridges
├── docs/playground/               # stretch-goal interactive demo
├── .cursor/rules/adaptron.mdc     # Cursor project rules (see STRUCTURE.md)
├── PRD.md
├── PLAN.md
├── pyproject.toml                 # zero-dependency core, optional extras
├── README.md
└── .gitignore
```

## 2. Core data model

### 2.1 `Agent`

- Wraps a callable (function, class instance with `__call__`, or a bridged
  third-party agent) plus its input/output types.
- Types come from, in priority order: (1) explicit declaration passed to
  `wrap()`, (2) inferred from Python type hints on the callable, (3)
  `Any` if neither is available.
- Exposes `.input_type`, `.output_type`, `.name`, and `.__call__`.

### 2.2 `Pipeline`

- Built by chaining `Agent`/`Pipeline` objects with `>>`.
- `a >> b` returns a `Pipeline` containing `[a, b]`; chaining further
  (`a >> b >> c`) flattens into `[a, b, c]`, not nested pipelines.
- At construction time, for each adjacent pair, `Pipeline` calls into the
  adapter registry to check compatibility (see §2.3) and inserts an
  adapter step where needed, or raises immediately if none exists.
- `pipeline.run(input)` executes stages in order, threading output to
  input, and logs each stage via `core/logging.py`.
- **Composability:** `Pipeline` exposes `.input_type` (its first stage's
  input type) and `.output_type` (its last stage's output type), the
  same public shape as `Agent`. This lets a fully-built `Pipeline` be
  used as the left- or right-hand side of `>>` like any other agent —
  `(a >> b) >> c` flattens `a >> b`'s stages into the outer pipeline and
  runs adapter resolution against its exposed `.output_type`, producing
  the same result as `a >> b >> c`.

### 2.3 Adapter registry

- Global registry: `dict[tuple[type, type], Callable]`.
- `register_adapter(source_type, target_type, fn)` adds an entry;
  re-registering the same pair overwrites with a warning (not a silent
  overwrite).
- Resolution at construction time: exact type match → no adapter needed;
  exact pair found in registry → insert adapter; otherwise → raise
  `NoAdapterError(source_type, target_type)` with a message suggesting
  the exact `register_adapter(...)` call needed to fix it.
- `Any` on either side of a connection skips adapter resolution entirely
  (treated as compatible, per PRD §6.2).
- **v1 scope note:** lookup is by exact `(type, type)` key — no MRO walk,
  no `isinstance`-based fallback. An adapter registered for a base class
  will *not* match a subclass instance. This keeps resolution O(1) and
  the error messages unambiguous, at the cost of requiring adapters to
  be registered per concrete type. Documented as a stated limitation in
  PRD §6.4, not a bug to silently work around; revisit only if real
  usage shows the exact-pair model is too restrictive (PRD §12).

### 2.4 Bridges

- Each bridge module exposes a single `can_wrap(obj) -> bool` and
  `adapt(obj) -> Agent` pair.
- `wrap()` in `adaptron/__init__.py` tries, in order: **LangChain bridge
  (if installed) → CrewAI bridge (if installed) → plain-Python
  detection**. First match wins.
- **This order is deliberate and matters for correctness.** A LangChain
  `AgentExecutor` or a CrewAI `Agent` is *also* a plain Python callable
  (it has `__call__` or a similarly-shaped method), so the generic
  plain-Python check would match it too. Framework bridges check for
  narrower, more specific signatures (e.g., `.invoke`/`.run` plus
  framework-specific attributes) and must run first; plain-Python
  detection is the catch-all and must run last, or every framework
  agent would be silently mis-wrapped as a generic callable and lose
  its bridge-specific calling convention and default types.
- Bridges are imported lazily inside `wrap()` (`try: import langchain`)
  so core never hard-depends on them.

## 3. Milestone-by-milestone implementation notes

Mirrors PRD §11, numbered 1-9 to match. [TASKS.md](./TASKS.md) prepends
a **Milestone 0** for one-time repo scaffolding (license, CI, pyproject
skeleton, Cursor rules) that has no corresponding PRD milestone since
it produces no product-facing behavior. Each milestone below should be
a separate branch/PR with its own tests before moving to the next.

### Milestone 1 — Core agent/port abstraction

- Implement `Agent`, type inference from `inspect.signature` +
  `typing.get_type_hints`.
- `wrap()` supports plain Python callables only; no pipeline yet.
- Introduce `core/errors.py` with the base `AdaptronError` exception and
  `WrapError` (raised when a callable/class doesn't expose a usable
  interface, per PRD §6.1). The hierarchy grows in later milestones
  (`NoAdapterError` in Milestone 3, `PipelineExecutionError` in
  Milestone 2) rather than being introduced all at once — see
  Milestone 7, which is an audit pass, not the starting point.
- Tests: wrapping a typed function, an untyped function (falls back to
  `Any`), a class with `__call__`, and a wrap failure that raises
  `WrapError` with an actionable message.

### Milestone 2 — Pipeline + `>>` operator

- Implement `Pipeline.__rshift__` / `__rrshift__` on `Agent` so `a >> b`
  works regardless of order of definition.
- Implement `Pipeline.input_type` / `.output_type` (derived from the
  first/last stage) so a `Pipeline` can be chained like an `Agent`
  (§2.2 composability) — verify `(a >> b) >> c` flattens identically to
  `a >> b >> c`.
- No adapter logic yet — mismatched types simply pass through (adapter
  registry is stubbed to always "match").
- Add `PipelineExecutionError` to `core/errors.py`, raised on `run()`
  when a stage fails, carrying which stage failed and the input it
  received (per PRD §6.6). Adapter-related failures come in Milestone 3.
- Tests: 2-stage and 3-stage plain pipelines run and produce correct
  output; flattening behavior (`a >> b >> c` is one `Pipeline`, not
  nested) is verified; nested composition (`(a >> b) >> c`) is
  verified; a mid-pipeline exception surfaces as `PipelineExecutionError`
  with the failing stage identified.

### Milestone 3 — Adapter registry + auto-adaptation

- Implement the registry and construction-time resolution described in
  §2.3, including the exact-pair-only lookup limitation.
- Add `NoAdapterError` to `core/errors.py`, raised at construction time
  with the two mismatched types and the exact `register_adapter(...)`
  call needed to fix it.
- Ship a small default adapter set: `str -> dict` (wraps as
  `{"text": ...}`), and one example custom `Message` class with a
  `str -> Message` adapter for docs/demo purposes.
- Tests: mismatched pipeline with a registered adapter auto-inserts it;
  mismatched pipeline with no adapter raises `NoAdapterError` at
  construction, not at `run()`; re-registering an existing pair
  overwrites with a warning (§2.3).

### Milestone 4 — Logging/observability layer

- Implement `core/logging.py` using stdlib `logging`, with a dedicated
  `adaptron` logger namespace.
- `Pipeline.run(input, verbose=True)` toggles per-stage log lines
  matching the PRD §8 format.
- Tests: capture log output via `caplog` and assert stage names/types
  appear in order.

### Milestone 5 — LangChain bridge

- `can_wrap` checks for LangChain's common agent/chain call interface
  (e.g., `.invoke` or `.run` method presence) without importing
  LangChain types directly into core.
- Wired into `wrap()` ahead of the plain-Python fallback, per the
  resolution order fixed in §2.4 — this is the first bridge probed.
- `adapt()` returns an `Agent` whose `__call__` delegates to the
  LangChain object's invoke method and whose types default to
  `str -> str` unless overridden.
- Tests gated behind `pytest.importorskip("langchain")`, including a
  regression test that a LangChain object is *not* mis-wrapped by the
  plain-Python fallback.

### Milestone 6 — CrewAI bridge

- Same pattern as Milestone 5, adapted to CrewAI's agent/task interface;
  probed after the LangChain bridge and before the plain-Python
  fallback (§2.4).
- Tests gated behind `pytest.importorskip("crewai")`.

### Milestone 7 — Error handling audit

- Not the introduction of `core/errors.py` — that hierarchy already
  exists incrementally from Milestone 1 (`WrapError`), Milestone 2
  (`PipelineExecutionError`), and Milestone 3 (`NoAdapterError`). This
  milestone is a consistency and completeness pass:
- Audit all raised exceptions against PRD §6.6: every error names the
  failing stage and the offending input/types.
- Verify every exception message is actionable without reading
  Adaptron's source (NFR: Debuggability, PRD §7).
- Add any missing edge-case errors surfaced during Milestones 1-6 (e.g.,
  an adapter function raising mid-conversion should be wrapped in a
  clear `AdaptronError` subclass rather than propagating a raw
  framework exception).

### Milestone 8 — Example pipelines + README

- `examples/cross_framework_pipeline.py`: one real LangChain agent, one
  real CrewAI agent, one plain Python formatter function, connected with
  `>>`, demonstrating at least one real auto-adaptation.
- README gets the before/after code comparison from the PRD's example
  usage section, plus install instructions for optional extras.

### Milestone 9 — Interactive demo/playground (stretch)

- Static site or notebook that replays a scripted/mocked version of the
  Milestone 8 example, showing the log output and final result visually.
- Explicitly labeled as illustrative per PRD §9 (avoids overstating a
  simulated demo as live execution).

## 4. Testing strategy

- Unit tests for every core module (`agent`, `pipeline`, `adapters`,
  `errors`, `logging`) with no optional dependencies required.
- Bridge tests are skipped in CI environments without `langchain`/
  `crewai` installed, but run in a dedicated CI job that installs the
  `[langchain]` and `[crewai]` extras.
- One end-to-end test per milestone-8 example, asserting the final
  pipeline output matches an expected value and that at least one
  adapter was invoked (checked via captured logs).

## 5. Tooling & CI

Necessary for the repo to hold up as production-grade OSS, not just as
a collection of passing tests locally:

- **Lint & format:** [ruff](https://docs.astral.sh/ruff/) for both
  linting and formatting, configured in `pyproject.toml`.
- **Type checking:** [mypy](https://mypy-lang.org/) run in strict mode
  over `adaptron/core/` (the bridges module is duck-typed by design and
  may need targeted `# type: ignore`s where third-party stubs are
  missing).
- **Pre-commit:** a `.pre-commit-config.yaml` running ruff and mypy on
  every commit, so CI failures are caught locally first.
- **CI workflow** (`.github/workflows/ci.yml`), matrixed across
  supported Python versions (3.10-3.12), with separate jobs:
  1. **Core tests** — install the package with no extras, run
     `pytest`, `ruff check`, and `mypy`.
  2. **Bridge tests** — install `adaptron[langchain,crewai]`, run the
     bridge-specific test files gated by `pytest.importorskip`.
  3. **Dependency isolation check** — install the bare package and
     assert `langchain`/`crewai` are absent from the environment
     (verifies PRD §8's "Dependency isolation" success metric
     mechanically, rather than by manual inspection).
- **Versioning:** Semantic Versioning starting at `0.x` during pre-1.0
  development (breaking changes allowed between minor versions until
  `1.0.0`); a `CHANGELOG.md` is updated per release (see
  [STRUCTURE.md](./STRUCTURE.md)).

## 6. Packaging

- `pyproject.toml` defines `adaptron` as the core package with no
  required dependencies, plus optional extras:
  ```toml
  [project.optional-dependencies]
  langchain = ["langchain>=0.2,<0.3"]
  crewai = ["crewai>=0.3,<0.4"]
  ```
  These ranges are illustrative — confirm current stable major versions
  for both frameworks at implementation time (Milestone 0) and pin
  accordingly; the exact bounds matter less than the *policy* of
  pinning tightly and revisiting deliberately.
- Version pins on extras are intentional (see PRD §9 risk: bridges break
  silently on upstream API changes) and should be revisited when bumping
  supported ranges.

## 7. Deferred design decisions (mirrors PRD §12)

These are implementation-level questions tied to PRD §12's Future
Considerations — only relevant if/when those post-v1 features are
picked up, not blockers for v1:

- If best-effort mode is added, should it live as a `Pipeline(strict=False)`
  flag, or a global config setting?
- If many-to-one adapter coercion is added, does registry lookup need to
  change from exact-pair matching to a resolution order (e.g.,
  MRO-based), and how would ambiguous matches be reported?
- If async agents are added, does `Pipeline` need a parallel `arun()`
  method, or should `run()` detect and await coroutines transparently?