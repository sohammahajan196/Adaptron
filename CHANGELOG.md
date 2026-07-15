# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Phase 0 scaffolding: package identity (`pyproject.toml`, MIT `LICENSE`, `.gitignore`),
  empty importable `adaptron` / `adaptron.core` / `adaptron.bridges` namespaces,
  Ruff / mypy / pytest tooling, pre-commit hooks, and GitHub Actions CI
  (core checks, bridge job stub, dependency-isolation check).
- `CHANGELOG.md` and contributor workflow docs (`CONTRIBUTING.md`).
- Phase 1 core agent/port abstraction: `AdaptronError` / `WrapError`,
  `Agent` with type inference (explicit → hints → `Any`), and plain-Python
  `wrap()` for functions and `__call__` instances (no framework bridges yet).
  Public exports: `wrap`, `Agent`.
- Phase 2 linear pipelines: `Pipeline` with the `>>` operator (flattens
  nested chains such as `(a >> b) >> c`), sync `run()` that threads stage
  outputs, and `PipelineExecutionError` for mid-pipeline failures.
  Public exports: `wrap`, `Agent`, `Pipeline`. Adapters still stubbed
  pending Phase 3.
- Phase 3 adapter registry and construction-time auto-adaptation:
  `register_adapter(source, target, fn)` with O(1) exact `(type, type)`
  lookup (no MRO/`isinstance` matching in v1), overwrite via
  `UserWarning`, and `NoAdapterError` raised when chaining with `>>` if
  types mismatch and no adapter is registered — never deferred to
  `run()`. Exact type match or `Any` on either side skips adaptation.
  Default adapters: `str → dict` (`{"text": ...}`) and demo
  `str → Message`. Public exports: `wrap`, `Agent`, `Pipeline`,
  `register_adapter`.
- Phase 4 logging/observability: stdlib `adaptron` logger with truncated
  stage previews; `Pipeline.run(..., verbose=False)` is silent by default
  and `verbose=True` emits one INFO line per agent and inserted adapter
  stage (name, in/out types, input/output previews) in execution order.
- Phase 5 LangChain bridge (optional extra `adaptron[langchain]`, pinned
  `langchain>=1.3,<1.4`): duck-typed `can_wrap`/`adapt` for Runnable and
  legacy Chain shapes; `wrap()` probes LangChain before the plain-Python
  catch-all (and before CrewAI, Phase 6); defaults bridged types to
  `str → str`. Bridge is skipped when the extra is not installed. Gated
  tests in `tests/test_bridges_langchain.py`.
