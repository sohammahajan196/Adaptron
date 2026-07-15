# Adaptron

**Connect AI agents from different frameworks into one pipeline — without writing glue code.**

> **Project status:** Phase 1 complete — `wrap` and `Agent` work for plain-Python
> callables. Pipelines, adapters, and framework bridges are not shipped yet.
> Track progress in [TASKS.md](./TASKS.md); full v1 target API is in
> [PRD.md](./PRD.md) / [PLAN.md](./PLAN.md).

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

Adaptron detects that the LangChain agent's output type doesn't match the CrewAI agent's expected input type, and automatically inserts a registered adapter to bridge them — logged, not silent. If no adapter exists for a given type pair, pipeline construction fails immediately with a clear error telling you exactly which `register_adapter(...)` call would fix it.

**Adaptron is not a new agent-building framework.** It doesn't create agents or make model calls on its own behalf — it's a thin, dependency-free connective layer over agents you've already built.

## Installation

```bash
pip install adaptron              # core library, zero third-party dependencies
pip install adaptron[langchain]   # + LangChain bridge
pip install adaptron[crewai]      # + CrewAI bridge
pip install adaptron[langchain,crewai]  # both
```

The core package never pulls in LangChain or CrewAI — framework support is strictly opt-in via extras.

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

Run with `verbose=True` to see exactly which stages and adapters executed:

```python
pipeline.run("hello adaptron", verbose=True)
# stage='to_upper' in=str out=str input='hello adaptron' output='HELLO ADAPTRON'
# stage='adapter<str->dict>' in=str out=dict input='HELLO ADAPTRON' output={'text': 'HELLO ADAPTRON'}
# stage='word_count' in=dict out=dict input={'text': 'HELLO ADAPTRON'} output={'words': 2}
```

See [`examples/`](./examples) for a runnable version of this, plus the flagship `cross_framework_pipeline.py` example combining a real LangChain agent, a real CrewAI agent, and a plain Python function.

## How it works

- **`wrap(agent)`** accepts a LangChain agent, a CrewAI agent, or any plain Python callable/class, and returns an `Agent` with an inferred (or explicit) input/output type.
- **`agent_a >> agent_b`** connects two agents (or pipelines) into a `Pipeline`. Type compatibility is checked immediately, at construction time — not deferred until you run it.
- **Mismatched types** are resolved by looking up a registered adapter for that exact `(source_type, target_type)` pair and inserting it automatically. No adapter registered → a clear error at construction time, not a silent failure at runtime.
- **Every stage is logged** (agent and adapter calls alike) with types and a truncated data preview, so a broken pipeline is diagnosable from log output alone.
- **The core library has zero required dependencies.** Framework support lives in optional, lazily-imported bridge modules — installing `adaptron` alone never pulls in LangChain or CrewAI.

For the full design — the `Agent`/`Pipeline` data model, adapter resolution algorithm, and bridge detection order — see [PLAN.md](./PLAN.md). For the complete requirements and v1 scope boundaries (what Adaptron deliberately does *not* do), see [PRD.md](./PRD.md).

## Project status & roadmap

Adaptron is under active initial development, built milestone-by-milestone (see [PLAN.md §3](./PLAN.md)):

1. Core agent/port abstraction
2. Pipeline + `>>` operator
3. Adapter registry + auto-adaptation
4. Logging/observability layer
5. LangChain bridge
6. CrewAI bridge
7. Error handling audit
8. Example pipelines + this README's flagship demo
9. *(Stretch)* Interactive playground

The phase-based implementation roadmap lives in [TASKS.md](./TASKS.md).

## Documentation

| Document | Purpose |
|---|---|
| [PRD.md](./PRD.md) | Product requirements — problem, goals, scope, user stories, success metrics |
| [PLAN.md](./PLAN.md) | Technical architecture — data model, resolution algorithms, milestones |
| [STRUCTURE.md](./STRUCTURE.md) | Repository layout and file-by-file rationale |
| [TASKS.md](./TASKS.md) | Phase-based implementation roadmap |

## Contributing

Contributions are welcome once the core scaffolding (Phase 0) lands. See [CONTRIBUTING.md](./CONTRIBUTING.md) for dev setup, how to run tests/lint/type-checks locally, and the one-phase-per-PR workflow this project follows.

## License

Adaptron will be released under the MIT License (recommended in [PRD.md §7](./PRD.md); the `LICENSE` file itself is added as part of Phase 0 scaffolding — see [TASKS.md](./TASKS.md)).
