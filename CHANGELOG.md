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
