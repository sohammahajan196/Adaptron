# Adaptron — Technical Plan

**Status:** Draft
**Related docs:** [PRD.md](./PRD.md) — product requirements this plan implements · [STRUCTURE.md](./STRUCTURE.md) — full repo layout and file-by-file rationale · [TASKS.md](./TASKS.md) — phase-based implementation roadmap

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
├── .cursor/rules/                 # Cursor project rules (see STRUCTURE.md)
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

Mirrors PRD §11, numbered 1-9 to match. [TASKS.md](./TASKS.md) turns these
into **Phases 0–9** (Phase 0 = scaffolding with no PRD counterpart) and
splits each into session-sized tasks with acceptance criteria. Prefer
one phase (or one Task X.Y) per branch/PR with tests before moving on.

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
  for both frameworks at implementation time (Phase 0 / Phase 5–6) and pin
  accordingly; the exact bounds matter less than the *policy* of
  pinning tightly and revisiting deliberately.
- Version pins on extras are intentional (see PRD §9 risk: bridges break
  silently on upstream API changes) and should be revisited when bumping
  supported ranges.

## 7. Post-v1 decisions made (mirrors PRD §12)

All five PRD §12 Future Considerations have shipped as **opt-in** post-v1
APIs (`TASKS.md` Post-v1 Backlog). Defaults are unchanged from v1: exact-pair
adapter lookup, strict construction-time failure, linear `>>` topology, and
sync-only `run()`. This section records the decisions actually made, so a
reader doesn't have to reverse-engineer them from the diff.

- **Best-effort mode** — shipped as a per-`Pipeline` flag, not a global
  config setting: `Pipeline(..., strict=False)`. When no adapter resolves
  for an adjacent pair, it warns (`UserWarning`, message prefixed
  `best-effort pipeline:`) and passes the value through unconverted instead
  of raising `NoAdapterError`. `strict=True` remains the dataclass default,
  so omitting the flag preserves v1 behavior exactly. The flag propagates
  through `>>` chaining (`Agent.__rshift__`/`__rrshift__`,
  `Pipeline.__rshift__`/`__rrshift__` all forward `strict`/`resolve_mro` from
  whichever side already carries them).
- **Subclass/MRO-aware adapter resolution** — shipped as
  `Pipeline(..., resolve_mro=True)`, backed by `get_adapter(source, target,
  mro=True)` in `adapters.py`. Resolution order: exact `(source_type,
  target_type)` match always wins first, regardless of `mro`; only when no
  exact pair exists does it walk `source_type.__mro__ ×
  target_type.__mro__`, preferring the shallowest source-MRO depth, then
  shallowest target-MRO depth (first hit in nested-loop order). Default
  remains `resolve_mro=False` (exact-pair only, v1 behavior).
- **Many-to-one adapter coercion** — no registry shape change was needed.
  Because the registry key is the full `(source_type, target_type)` tuple,
  registering `TypeA -> Target` and `TypeB -> Target` never collides —
  each is a distinct key. The existing warn-on-overwrite path only fires
  when the *same* `(source_type, target_type)` pair is registered twice, so
  it correctly leaves legitimate many-to-one registrations alone. Combined
  with MRO resolution above, one base-class adapter can also serve many
  subclasses without per-subclass registration.
- **Branching/parallel pipeline topology** — shipped as a standalone helper,
  `parallel(*agents, name="parallel") -> Agent`, in `pipeline.py`, not a new
  `Pipeline` topology or a multi-input/output port system. It fans one input
  out to every branch (in order) and collects results into a `tuple`,
  exposing itself as a normal `Agent` (`output_type=tuple`) so it composes
  with `>>` like any other stage — e.g. `parallel(a, b) >> merge_fn`. Each
  branch call is independent (no shared mutable state between branches);
  execution is still synchronous/sequential per branch unless awaited via
  `arun()`. `parallel` is exported from `adaptron/__init__.py` as a
  documented post-v1 addition to the otherwise-small public API.
- **Native async execution** — shipped as `Pipeline.arun()`, a separate
  coroutine method alongside sync `run()`, not transparent coroutine
  detection inside `run()`. `arun()` awaits any stage output that
  `inspect.isawaitable()` flags; sync stages pass through unchanged. `run()`
  deliberately does **not** silently await — if a stage returns an
  awaitable, `run()` raises `AdaptronError` pointing the caller at
  `arun()`, so mixing a sync pipeline with an async stage fails loudly
  rather than returning a coroutine object as if it were a real result.
  No new dependency was introduced — `arun()` uses stdlib `asyncio`/
  `inspect.isawaitable` only (see `dependencies.mdc`).