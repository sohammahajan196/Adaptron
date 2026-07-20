# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-07-20

First public alpha of Adaptron: typed agent wrapping, linear pipelines with
construction-time adapters, optional LangChain/CrewAI bridges, and runnable
examples. Package version is `0.1.0` in `pyproject.toml`. Tag `v0.1.0` when
you are ready to cut the GitHub release.

### Added

- Phase 0 scaffolding: package identity (`pyproject.toml`, MIT `LICENSE`,
  `.gitignore`), empty importable `adaptron` / `adaptron.core` /
  `adaptron.bridges` namespaces, Ruff / mypy / pytest tooling, pre-commit
  hooks, and GitHub Actions CI (core checks, bridge job, dependency-isolation
  check).
- `CHANGELOG.md` and contributor workflow docs (`CONTRIBUTING.md`).
- Phase 1 core agent/port abstraction: `AdaptronError` / `WrapError`,
  `Agent` with type inference (explicit → hints → `Any`), and plain-Python
  `wrap()` for functions and `__call__` instances. Public exports: `wrap`,
  `Agent`.
- Phase 2 linear pipelines: `Pipeline` with the `>>` operator (flattens
  nested chains such as `(a >> b) >> c`), sync `run()` that threads stage
  outputs, and `PipelineExecutionError` for mid-pipeline failures. Public
  exports: `wrap`, `Agent`, `Pipeline`.
- Phase 3 adapter registry and construction-time auto-adaptation:
  `register_adapter(source, target, fn)` with O(1) exact `(type, type)`
  lookup (no MRO/`isinstance` matching in v1), overwrite via `UserWarning`,
  and `NoAdapterError` raised when chaining with `>>` if types mismatch and
  no adapter is registered — never deferred to `run()`. Exact type match or
  `Any` on either side skips adaptation. Default adapters: `str → dict`
  (`{"text": ...}`) and demo `str → Message`. Public exports: `wrap`,
  `Agent`, `Pipeline`, `register_adapter`.
- Phase 4 logging/observability: stdlib `adaptron` logger with truncated
  stage previews; `Pipeline.run(..., verbose=False)` is silent by default
  and `verbose=True` emits one INFO line per agent and inserted adapter
  stage (name, in/out types, input/output previews) in execution order.
- Phase 5 LangChain bridge (optional extra `adaptron[langchain]`, pinned
  `langchain>=1.3,<1.4`): duck-typed `can_wrap`/`adapt` for Runnable and
  legacy Chain shapes; `wrap()` probes LangChain before CrewAI and the
  plain-Python catch-all; defaults bridged types to `str → str`. Bridge is
  skipped when the extra is not installed. Gated tests in
  `tests/test_bridges_langchain.py`.
- Phase 6 CrewAI bridge (optional extra `adaptron[crewai]`, pinned
  `crewai>=1.15,<1.16`): duck-typed `can_wrap`/`adapt` for Agent
  (`role`/`goal`/`kickoff`) and Crew (`agents`/`tasks`/`kickoff`) shapes;
  `wrap()` probe order is LangChain → CrewAI → plain-Python; defaults
  bridged types to `str → str` (Crew non-dict inputs become
  `{"input": value}`; framework outputs unwrap `.raw` when present). Bridge
  is skipped when the extra is not installed. Gated tests in
  `tests/test_bridges_crewai.py`. Install both bridges with
  `adaptron[langchain,crewai]`.
- Phase 7 error-handling polish: raise-site audit so messages stay
  actionable without reading source; empty `Pipeline` / non-callable
  `Agent` raise `AdaptronError` / `WrapError` (not bare stdlib exceptions);
  adapter conversion failures during `run()` wrap as
  `PipelineExecutionError` with stage name, input preview, and
  `source_type`/`target_type` (never pass bad data downstream).
  Message-contract tests in `tests/test_errors.py`.
- Phase 8 examples and README proof:
  `examples/plain_python_pipeline.py` (bare install quickstart),
  `examples/cross_framework_pipeline.py` (LangChain → `Message→str` adapter
  → CrewAI → plain formatter; `--mock` default / `--live` with
  `OPENAI_API_KEY`), e2e coverage in `tests/test_examples.py`, and a README
  aligned with the shipped public API (`wrap`, `Agent`, `Pipeline`,
  `register_adapter`).
