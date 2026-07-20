# Adaptron

**Connect AI agents from different frameworks into one pipeline — without writing glue code.**

![Illustrative flagship pipeline animation](./docs/demo-flagship.svg)

*Illustrative diagram (not a live run). Interactive scripted replay:
[`docs/playground/index.html`](./docs/playground/index.html).*

## Features

| Area | What's shipped |
|---|---|
| **Core pipeline** | `wrap()`, `Agent`, linear `Pipeline`, `>>` chaining with construction-time type checks |
| **Auto-adaptation** | Adapter registry + automatic adapter insertion; default `str → dict` and demo `str → Message` |
| **Framework bridges** | Optional LangChain and CrewAI bridges (`adaptron[langchain]`, `adaptron[crewai]`) |
| **Best-effort mode** | `Pipeline(..., strict=False)` — warn and passthrough when no adapter (default still strict) |
| **MRO-aware resolution** | `Pipeline(..., resolve_mro=True)` — subclass / base-class adapter lookup |
| **Branching / parallel** | `parallel(a, b, ...)` fan-out helper → `tuple` of branch outputs |
| **Async support** | `await pipeline.arun(...)` for async stages; sync `run()` rejects awaitables |
| **Observability** | `verbose=True` stage logging (agents + inserted adapters) |
| **Examples & docs** | Runnable scripts in [`examples/`](./examples/); illustrative playground in [`docs/playground/`](./docs/playground/) |

**Status:** **v0.1.0** (2026-07-20) — Phases 0–9 complete, including post-v1 backlog
and the stretch playground. Top-level exports: `wrap`, `Agent`, `Pipeline`,
`register_adapter`, `parallel`. See [CHANGELOG.md](./CHANGELOG.md); design docs:
[PRD.md](./PRD.md) / [PLAN.md](./PLAN.md).

---

## The problem

Multi-agent AI systems increasingly combine agents from different frameworks — LangChain, CrewAI, plain Python functions — in the same pipeline. Each framework has its own conventions for input/output shapes: raw strings, framework-specific message objects, dicts, Pydantic models. Connecting them today means writing a custom conversion function for every incompatible pair, and re-deriving it every time an agent gets swapped out.

### Before Adaptron

```python
# Manual glue code between a LangChain agent and a CrewAI agent
langchain_output = langchain_agent.invoke({"input": user_query})
# LangChain gives back an AIMessage; CrewAI expects a dict.
crewai_input = {"text": langchain_output.content}
crewai_output = crewai_agent.execute(crewai_input)
# ...and now write it again for the *next* pair of agents you connect.
```

### After Adaptron

```python
from adaptron import wrap

pipeline = wrap(langchain_agent) >> wrap(crewai_agent) >> wrap(format_result)
result = pipeline.run(user_query)
```

Adaptron detects that the LangChain agent's output type doesn't match the CrewAI agent's expected input type, and automatically inserts a registered adapter to bridge them — logged when `verbose=True`, not silent. If no adapter exists for a given type pair, pipeline construction fails immediately with a clear error telling you exactly which `register_adapter(...)` call would fix it.

**Adaptron is not a new agent-building framework.** It doesn't create agents or make model calls on its own behalf — it's a thin, dependency-free connective layer over agents you've already built.

## Installation

Requires **Python 3.10+**.

```bash
pip install adaptron                        # core library, zero third-party dependencies
pip install adaptron[langchain]             # + LangChain bridge (pinned langchain>=1.3,<1.4)
pip install adaptron[crewai]                # + CrewAI bridge (pinned crewai>=1.15,<1.16)
pip install adaptron[langchain,crewai]      # both bridges
pip install adaptron[dev]                   # pytest, ruff, mypy, pre-commit (dev/CI tooling only)
pip install adaptron[langchain,crewai,dev]    # bridges + dev tooling
```

For local development from a clone:

```bash
pip install -e ".[dev]"                       # core + dev tooling
pip install -e ".[langchain,crewai,dev]"    # + both bridges
```

The core package never pulls in LangChain or CrewAI — framework support is strictly opt-in via extras. `wrap()` probes most-specific first: LangChain (if installed) → CrewAI (if installed) → plain-Python callable. Each bridge is skipped entirely when its extra isn't present.

## Quickstart

```python
from adaptron import wrap

def to_upper(text: str) -> str:
    return text.upper()

def word_count(payload: dict) -> dict:
    return {"words": len(payload["text"].split())}

# Default str -> dict adapter inserts automatically (exact type match only).
pipeline = wrap(to_upper) >> wrap(word_count)
print(pipeline.run("hello adaptron"))
# {'words': 2}
```

Run with `verbose=True` to see exactly which stages and adapters executed (configure logging if you want the lines on stderr):

```python
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

pipeline.run("hello adaptron", verbose=True)
# stage='to_upper' in=str out=str input='hello adaptron' output='HELLO ADAPTRON'
# stage='adapter<str->dict>' in=str out=dict input='HELLO ADAPTRON' output={'text': 'HELLO ADAPTRON'}
# stage='word_count' in=dict out=dict input={'text': 'HELLO ADAPTRON'} output={'words': 2}
```

Public API (`adaptron.__all__`): `wrap`, `Agent`, `Pipeline`, `register_adapter`,
`parallel`. Pipeline methods `run()` and `arun()` are the sync/async execution
entry points (not top-level exports).

## Examples

Runnable scripts live in [`examples/`](./examples/):

| Script | What it shows | Needs |
|---|---|---|
| [`plain_python_pipeline.py`](./examples/plain_python_pipeline.py) | README quickstart: `wrap` + `>>` + default `str→dict` adapter | bare `adaptron` |
| [`cross_framework_pipeline.py`](./examples/cross_framework_pipeline.py) | LangChain → auto `Message→str` adapter → CrewAI → plain formatter | `adaptron[langchain,crewai]`; `--mock` (default, no API keys) or `--live` (`OPENAI_API_KEY`) |

```bash
python examples/plain_python_pipeline.py --verbose
python examples/cross_framework_pipeline.py --verbose
```

## Illustrative playground (stretch)

Open [`docs/playground/index.html`](./docs/playground/index.html) for a
**simulated** walkthrough of the flagship cross-framework pipeline (diagram +
scripted verbose-style logs).

This playground does **not** execute Adaptron, LangChain, CrewAI, or any LLM —
outputs are pre-scripted for docs (`PRD.md` §9). For a real run, use
[`examples/cross_framework_pipeline.py`](./examples/cross_framework_pipeline.py)
(`--mock` needs no API keys; `--live` needs `OPENAI_API_KEY`). See
[`docs/playground/README.md`](./docs/playground/README.md) for format notes.

## How it works

- **`wrap(agent)`** accepts a LangChain agent/chain, a CrewAI agent/crew, or any plain Python callable (functions and `__call__` instances — not bare classes), and returns an `Agent` with an inferred (or explicit) input/output type.
- **`agent_a >> agent_b`** connects two agents (or pipelines) into a `Pipeline`. Type compatibility is checked immediately, at construction time — not deferred until you run it.
- **Mismatched types** are resolved by looking up a registered adapter for that exact `(source_type, target_type)` pair and inserting it automatically. Exact match only by default (no MRO/`isinstance` fallback). Opt in with `Pipeline(..., resolve_mro=True)` for subclass / many-to-one base adapters. No adapter registered → `NoAdapterError` at construction time unless `Pipeline(..., strict=False)` (best-effort warn + passthrough). Defaults include `str → dict` and demo `str → Message`.
- **`parallel(a, b, ...)`** (post-v1) fans one input out to several agents and returns a `tuple` of results (still sync/sequential under the hood).
- **`Pipeline.run` / `arun`**: sync `run()` by default; `await pipeline.arun(...)` when stages are async. `run()` errors if a stage returns an awaitable.
- **Every stage is logged** when `Pipeline.run(..., verbose=True)` (agent and adapter calls alike) with types and a truncated data preview, so a broken pipeline is diagnosable from log output alone.
- **The core library has zero required dependencies.** Framework support lives in optional, lazily-imported bridge modules — installing `adaptron` alone never pulls in LangChain or CrewAI.

For the full design — the `Agent`/`Pipeline` data model, adapter resolution algorithm, and bridge detection order — see [PLAN.md](./PLAN.md). For the complete requirements and v1 scope boundaries (what Adaptron deliberately does *not* do), see [PRD.md](./PRD.md).

## Project status & roadmap

Adaptron is built milestone-by-milestone (see [PLAN.md §3](./PLAN.md) / [TASKS.md](./TASKS.md)):

| # | Milestone | Status |
|---|---|---|
| 0 | Repository scaffolding | Done |
| 1 | Core agent/port abstraction | Done |
| 2 | Pipeline + `>>` operator | Done |
| 3 | Adapter registry + auto-adaptation | Done |
| 4 | Logging/observability | Done |
| 5 | LangChain bridge | Done |
| 6 | CrewAI bridge | Done |
| 7 | Error handling audit | Done |
| 8 | Example pipelines + README | Done (`0.1.0`) |
| 9 | Interactive playground | Done (stretch — illustrative static replay only) |

## Documentation

| Document | Purpose |
|---|---|
| [PRD.md](./PRD.md) | Product requirements — problem, goals, scope, user stories, success metrics |
| [PLAN.md](./PLAN.md) | Technical architecture — data model, resolution algorithms, milestones |
| [STRUCTURE.md](./STRUCTURE.md) | Repository layout and file-by-file rationale |
| [TASKS.md](./TASKS.md) | Phase-based implementation roadmap |
| [CHANGELOG.md](./CHANGELOG.md) | Released notes (`0.1.0`) and `[Unreleased]` |
| [docs/playground/](./docs/playground/) | Illustrative (non-live) flagship pipeline replay |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Dev setup, CI expectations, actionable-error guidance |

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md) for editable install, how to run tests/lint/type-checks locally, and the one-phase-per-PR workflow this project follows.

## License

Adaptron is released under the [MIT License](./LICENSE).
