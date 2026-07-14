# Adaptron — Execution Checklist

**Status:** Not started — no implementation exists yet.
**Related docs:** [PRD.md](./PRD.md) (what/why) · [PLAN.md](./PLAN.md) (architecture and milestone rationale) · [STRUCTURE.md](./STRUCTURE.md) (repo layout)

---

## Purpose of this document

`PLAN.md` describes *what each milestone must achieve* and the architectural reasoning behind it — it should stay stable and only change when the design itself changes. This document breaks each milestone into small, literal, checkable tasks meant to be ticked off as implementation proceeds. Expect `TASKS.md` to be edited constantly; expect `PLAN.md` to barely change.

Check off items with `[x]` as they're completed. Each milestone should ship as its own branch/PR with passing tests before the next one starts (`PLAN.md §3`).

---

## Milestone 0 — Repository scaffolding

No product behavior yet; this unblocks every later milestone.

- [ ] Initialize `pyproject.toml`: package name `adaptron`, Python `>=3.10`, zero required dependencies, `[project.optional-dependencies]` stub for `langchain`/`crewai`.
- [ ] Add `ruff` and `mypy` configuration to `pyproject.toml`.
- [ ] Add `.pre-commit-config.yaml` running `ruff check`, `ruff format --check`, and `mypy`.
- [ ] Add `.gitignore` (`__pycache__/`, `*.egg-info/`, `dist/`, `build/`, `.pytest_cache/`, `.mypy_cache/`, `.venv/`).
- [ ] Choose and add a `LICENSE` file (MIT recommended — `PRD.md §7`).
- [ ] Create `.github/workflows/ci.yml` with the three jobs from `PLAN.md §5` (core tests, bridge tests, dependency-isolation check).
- [ ] Author `.cursor/rules/adaptron.mdc` capturing the non-negotiables listed in `STRUCTURE.md`.
- [ ] Create empty package skeleton: `adaptron/__init__.py`, `adaptron/core/__init__.py`, `adaptron/bridges/__init__.py`, `tests/__init__.py`.
- [x] Write `CONTRIBUTING.md` (dev setup, how to run tests/lint locally, PR expectations).
- [ ] Create empty `CHANGELOG.md` with an `[Unreleased]` heading.
- [ ] Confirm CI passes on an empty package (no tests yet, but lint/type-check jobs should run green).

## Milestone 1 — Core agent/port abstraction

- [ ] Implement `core/errors.py` with `AdaptronError` (base) and `WrapError`.
- [ ] Implement `Agent` in `core/agent.py`: wraps a callable, exposes `.input_type`, `.output_type`, `.name`, `.__call__`.
- [ ] Implement type resolution priority: explicit types passed to `wrap()` → `typing.get_type_hints()` on the callable → `Any` fallback.
- [ ] Implement `wrap()` in `adaptron/__init__.py` supporting plain Python functions and callable class instances only (no bridges yet).
- [ ] Raise `WrapError` with an actionable message when wrapping fails (e.g., object isn't callable).
- [ ] Export `wrap` and `Agent` from `adaptron/__init__.py`.
- [ ] Write `tests/test_agent.py`: typed function, untyped function (falls back to `Any`), callable class instance, and a wrap failure case.
- [ ] Update `CHANGELOG.md`.

## Milestone 2 — Pipeline + `>>` operator

- [ ] Implement `PipelineExecutionError` in `core/errors.py`.
- [ ] Implement `Pipeline` in `core/pipeline.py`: stores an ordered list of stages.
- [ ] Implement `Agent.__rshift__` / `__rrshift__` so `a >> b` returns a `Pipeline`.
- [ ] Implement flattening: `a >> b >> c` produces one `Pipeline([a, b, c])`, not nested pipelines.
- [ ] Implement `Pipeline.__rshift__` so a `Pipeline` can appear on either side of `>>` (composability).
- [ ] Implement `Pipeline.input_type` / `.output_type` derived from the first/last stage.
- [ ] Implement `Pipeline.run(input)` executing stages in order, threading output to input.
- [ ] Wrap stage failures in `PipelineExecutionError`, naming the failing stage and the input it received.
- [ ] Export `Pipeline` from `adaptron/__init__.py`.
- [ ] Write `tests/test_pipeline.py`: 2-stage run, 3-stage run, flattening assertion, nested composition (`(a >> b) >> c`), and a failing-stage test asserting `PipelineExecutionError` context.
- [ ] Update `CHANGELOG.md`.

## Milestone 3 — Adapter registry + auto-adaptation

- [ ] Implement `NoAdapterError` in `core/errors.py`.
- [ ] Implement the adapter registry in `core/adapters.py`: `dict[tuple[type, type], Callable]`.
- [ ] Implement `register_adapter(source_type, target_type, fn)`, with a warning (not silent overwrite) when re-registering an existing pair.
- [ ] Implement construction-time resolution in `Pipeline`: exact type match → no-op; registered pair → insert adapter stage; `Any` on either side → skip resolution; otherwise → raise `NoAdapterError` naming both types and the exact `register_adapter(...)` call to fix it.
- [ ] Ship default adapters: `str -> dict`, plus an example `Message` class with a `str -> Message` adapter for docs/demo use.
- [ ] Export `register_adapter` from `adaptron/__init__.py`.
- [ ] Write `tests/test_adapters.py`: auto-insertion on a registered mismatch, `NoAdapterError` at construction time (not at `run()`) for an unregistered mismatch, and the re-registration warning.
- [ ] Update `CHANGELOG.md`.

## Milestone 4 — Logging/observability layer

- [ ] Implement `core/logging.py` using stdlib `logging` under an `adaptron` logger namespace.
- [ ] Add a `verbose` flag to `Pipeline.run(input, verbose=True)`.
- [ ] Log each stage (agent or adapter) with: name, input type, output type, truncated input/output preview.
- [ ] Ensure logging requires no external dependencies and is silent by default.
- [ ] Write logging tests using `caplog`, asserting stage names/types appear in the correct order.
- [ ] Update `CHANGELOG.md`.

## Milestone 5 — LangChain bridge

- [ ] Implement `bridges/langchain_bridge.py`: `can_wrap(obj) -> bool` (checks for `.invoke`/`.run`) and `adapt(obj) -> Agent`.
- [ ] Default bridged-agent types to `str -> str` unless overridden.
- [ ] Wire the bridge into `wrap()` **ahead of** the plain-Python fallback (`PLAN.md §2.4`).
- [ ] Ensure `langchain` is imported lazily (inside a `try/except ImportError`), never at module load time in core.
- [ ] Add `langchain` as an optional extra in `pyproject.toml`, pinned to a confirmed current stable range.
- [ ] Write `tests/test_bridges_langchain.py` gated by `pytest.importorskip("langchain")`, including a regression test proving a LangChain object is not mis-wrapped by the plain-Python fallback.
- [ ] Update `CHANGELOG.md`.

## Milestone 6 — CrewAI bridge

- [ ] Implement `bridges/crewai_bridge.py` following the same `can_wrap`/`adapt` pattern as Milestone 5, adapted to CrewAI's agent/task interface.
- [ ] Wire the bridge into `wrap()` after the LangChain bridge and before the plain-Python fallback.
- [ ] Add `crewai` as an optional extra in `pyproject.toml`, pinned to a confirmed current stable range.
- [ ] Write `tests/test_bridges_crewai.py` gated by `pytest.importorskip("crewai")`.
- [ ] Update `CHANGELOG.md`.

## Milestone 7 — Error handling audit

This is a review pass, not new-feature work — `errors.py` already exists incrementally from Milestones 1-3.

- [ ] Audit every raised exception against `PRD.md §6.6`: does it name the failing stage and the offending input/type?
- [ ] Confirm every error message is actionable without reading source (spot-check with someone unfamiliar with the codebase, if possible).
- [ ] Handle the case of an adapter function itself raising mid-conversion — wrap it in a clear `AdaptronError` subclass rather than letting a raw exception propagate.
- [ ] Write `tests/test_errors.py` covering each exception type's message content, not just its type.
- [ ] Update `CHANGELOG.md`.

## Milestone 8 — Example pipelines + README

- [ ] Write `examples/plain_python_pipeline.py`: minimal wrapped-function pipeline, no adapters needed.
- [ ] Write `examples/cross_framework_pipeline.py`: one real LangChain agent, one real CrewAI agent, one plain Python formatter, connected with `>>`, demonstrating at least one genuine auto-adaptation.
- [ ] Add an end-to-end test per example, asserting final output and that at least one adapter was invoked (via captured logs).
- [ ] Write the full `README.md` per the structure in this repo's current draft: pitch, before/after comparison, install instructions, quickstart, links to docs.
- [ ] Record a short GIF/terminal recording of the flagship example for the README (per `PRD.md §3.2`).
- [ ] Update `CHANGELOG.md` — this is a good point to consider tagging `v0.1.0`.

## Milestone 9 — Interactive demo/playground (stretch)

- [ ] Decide on format: static site vs. notebook.
- [ ] Build a scripted/mocked replay of the Milestone 8 flagship example (diagram + log output).
- [ ] Explicitly label all output as illustrative/simulated, not live execution (`PRD.md §9`).
- [ ] Link the playground from `README.md`.

---

## Backlog (post-v1 — not scheduled)

Tracks `PRD.md §12` / `PLAN.md §7`. Do not start these until Milestone 8 has shipped and the core API has had real usage:

- [ ] Best-effort mode (`Pipeline(strict=False)` or equivalent).
- [ ] Subclass/MRO-aware adapter resolution.
- [ ] Many-to-one adapter coercion.
- [ ] Branching/parallel pipeline topology.
- [ ] Native async execution (`arun()`).
