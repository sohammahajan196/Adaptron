# Product Requirements Document: Adaptron — Composable AI Agent Framework

**Status:** Draft
**Version:** 1.0
**Scope:** MVP (core library + one working cross-framework demo pipeline)
**Related docs:** [PLAN.md](./PLAN.md) (architecture and milestones implementing this PRD) · [STRUCTURE.md](./STRUCTURE.md) (repo layout) · [TASKS.md](./TASKS.md) (execution checklist) · [README.md](./README.md) (project entry point)

---

## 1. Summary

Adaptron is a lightweight Python framework that lets AI agents built on different frameworks (LangChain, CrewAI, plain Python) connect into a single pipeline, regardless of their underlying data formats. Agents expose typed input/output ports; when two connected agents have mismatched types, Adaptron automatically inserts a registered adapter to reshape the data so the handoff still works. The product's core value proposition is **interoperability without glue code**, not a new agent-building framework.

## 2. Problem Statement

Developers building multi-agent AI systems increasingly combine agents from different frameworks — LangChain, CrewAI, and custom Python classes — within the same pipeline. Each framework has its own conventions for input/output data shapes (raw strings, framework-specific message objects, dicts, Pydantic models). Connecting agents across frameworks currently requires:

- Writing custom conversion functions for every pair of incompatible agents.
- Re-deriving these conversions any time an agent is swapped out.
- No standard way to inspect *what* got converted and *why*, making pipelines hard to debug.

There is no lightweight, framework-agnostic layer that handles this interoperability automatically while staying out of the way otherwise.

## 3. Goals

### 3.1 Product goals

- Let a developer wrap an existing agent (LangChain, CrewAI, or plain Python) in one line of code.
- Let developers chain wrapped agents into a pipeline using a simple, readable syntax.
- Automatically detect input/output type mismatches between connected agents and resolve them with a registered adapter.
- Make the adaptation step visible and inspectable (logged, not a silent black box).
- Keep the core library free of hard dependencies on LangChain, CrewAI, or any other third-party framework.

### 3.2 Business/portfolio goals

- Demonstrate real systems/API design thinking (typed interfaces, adapter resolution, duck-typed bridging) as a portfolio-quality project, distinct from a typical "I built an agent with LangChain" project.
- Keep the project demoable — a visitor should be able to see the core value prop (auto-adaptation between mismatched agents) in under a minute, via README GIF or live playground.

### 3.3 Non-goals (explicit out of scope)

- Not a framework for building new agents from scratch — Adaptron wraps existing agents, it does not create them.
- Not a distributed/multi-host orchestration system in v1 — single-process, linear pipelines only.
- Not a hosted, production-grade orchestration service.
- No automatic (LLM-inferred) transform generation in v1 — adapters are explicitly registered, not inferred at runtime.
- No branching/parallel pipeline topology in v1 — strictly linear (`>>` chain) execution.
- No async agent execution in v1 — `pipeline.run()` is synchronous only. Async LLM calls must be wrapped in a synchronous callable (e.g., via `asyncio.run`) before being passed to `wrap()`. Native async support (an `arun()` counterpart) is a candidate for a post-v1 release once the sync API has proven itself.

## 4. Target Users & Personas

| Persona | Description | Needs from the product |
|---|---|---|
| Multi-framework developer | Has agents built across LangChain, CrewAI, and/or plain Python and wants them to interoperate | One-line wrapping, no manual conversion code, confidence that swapping an agent later won't break the pipeline |
| Framework-agnostic builder | Deliberately avoids locking into one agent framework's abstractions | A neutral connective layer that doesn't force adoption of any single framework's conventions |
| Evaluator (recruiter/engineer) | Browsing the project on GitHub to judge engineering ability, not adopting it for production use | A clear before/after code comparison, a working demo/GIF, and readable source code that shows deliberate design decisions |

## 5. Use Cases / User Stories

1. As a developer, I want to wrap an existing LangChain agent in one line, so I can use it inside a pipeline without rewriting it to match a new interface.
2. As a developer, I want to connect a LangChain agent's output directly to a CrewAI agent's input, even though their expected data types don't match, so I don't have to write a manual conversion function myself.
3. As a developer, I want to see a log of exactly which adapter was applied and why, so I can debug a pipeline instead of treating the conversion as a black box.
4. As a developer, I want pipeline construction to fail early with a clear error if no adapter exists for a type mismatch, rather than failing silently or late at run time.
5. As a developer, I want to register my own custom adapter for a type pair Adaptron doesn't know about, so the system remains extensible to my own data types.
6. As an evaluator, I want to see a short, runnable example proving that two agents from different frameworks were connected and the type mismatch was actually resolved, so I can trust the interoperability claim isn't just theoretical.

## 6. Functional Requirements

### 6.1 Agent wrapping

- `wrap(agent)` accepts a LangChain agent, CrewAI agent, or plain Python callable/class and returns an Adaptron-compatible agent object.
- `agent_type` (LangChain / CrewAI / plain Python) is never passed explicitly by the caller — it is detected automatically at wrap time and determines which bridge module handles the agent. Detection is ordered from most specific to least specific: framework bridges are probed first (they check for framework-specific method signatures), with the plain-Python callable check used only as the final catch-all. This ordering matters because a LangChain or CrewAI agent object is *also* a plain Python callable — if the generic check ran first, it would silently absorb framework agents that should have gone through a bridge (see [PLAN.md §2.4](./PLAN.md) for the resolution order).
- Wrapping must not require importing LangChain or CrewAI inside Adaptron's core — detection/adaptation happens via duck typing (checking for known method signatures at wrap time) inside separate, optional bridge modules.
- If wrapping fails (agent doesn't expose a usable interface), raise a clear, actionable error message.
- Every wrapped agent accepts exactly one input value and returns exactly one output value. Multi-argument framework calls (e.g., a LangChain chain invoked with `{"input": ..., "chat_history": ...}`) are represented as a single `dict`-typed value, not as multiple ports. Adaptron does not support multi-input or multi-output ports in v1.

### 6.2 Ports and type declaration

- Each wrapped agent must expose (or infer) an input type and an output type.
- Types can be Python primitives (`str`, `dict`, `list`) or user-defined classes (e.g., Pydantic models).
- If an agent doesn't explicitly declare types, Adaptron should attempt to infer them from type hints; if that fails, treat the port as untyped (`Any`) and skip adapter-matching for it.

### 6.3 Pipeline construction

- Agents connect via the `>>` operator: `pipeline = agent_a >> agent_b >> agent_c`.
- Type compatibility between connected agents is checked at construction time, not deferred to run time.
- A `Pipeline` is itself composable: it exposes the input type of its first stage and the output type of its last stage, so a fully-built pipeline can be treated as a single agent and chained into a larger pipeline (e.g., `(agent_a >> agent_b) >> agent_c` behaves identically to `agent_a >> agent_b >> agent_c`).

### 6.4 Auto-adaptation

- Adaptron maintains a registry of known adapters (e.g., `str -> Message`, `dict -> BaseModel`).
- When two connected agents' output/input types don't match exactly:
  - If a registered adapter exists for that exact type pair, insert it automatically into the pipeline.
  - If no adapter exists, raise a clear error at construction time naming the two mismatched types and suggesting the user register a custom adapter.
- Developers can register custom adapters: `register_adapter(source_type, target_type, fn)`.
- **v1 limitation (by design, not an oversight):** resolution is an exact `(source_type, target_type)` pair lookup. It does not walk the MRO of either type, so an adapter registered for a base class will not automatically apply to a subclass instance. Developers must register adapters for the concrete types their agents actually produce/consume. Subclass-aware resolution is a candidate future enhancement — see §12.

### 6.5 Execution & observability

- `pipeline.run(input)` executes the full pipeline in order.
- Every stage (agent call and adapter call) is logged with: agent/adapter name, input type, output type, and a truncated input/output preview.
- Logging is toggleable (verbose vs. silent) and requires no external dependencies.

### 6.6 Error handling

- If an agent raises an exception mid-pipeline, execution halts and the error surfaces with context: which stage failed, what input it received.
- If an adapter fails to convert data (e.g., malformed input), a clear error is raised rather than silently passing bad data downstream.

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Dependencies | Core package has zero required third-party dependencies; LangChain/CrewAI support ships as optional extras (e.g., `pip install adaptron[langchain]`) |
| Compatibility | Python 3.10+ support |
| Performance | Core pipeline overhead is negligible relative to the LLM calls themselves — no meaningful added latency from wrapping, port checks, or adapters |
| Debuggability | A new user should be able to diagnose a broken pipeline from log output alone, without reading Adaptron's source |
| Extensibility | Adding a new adapter or a new framework bridge should not require modifying core pipeline logic |
| Portability | The library should work identically in a script, notebook, or CI environment with no environment-specific behavior |
| Licensing | Released under a permissive open-source license (MIT recommended) to maximize adoption and portfolio visibility |

## 8. Success Metrics

Since this is a portfolio/open-source project rather than a monetized product, success is measured technically and by demo clarity rather than commercially:

- **Core workflow simplicity**: a developer can wrap one LangChain agent, one CrewAI agent, and one plain Python function, connect them with `>>`, and run a working pipeline in under 10 lines of code.
- **Adaptation correctness**: the built-in example pipeline demonstrates at least one genuine type mismatch resolved automatically, with log output as proof.
- **Dependency isolation**: `pip install adaptron` pulls in zero LangChain/CrewAI dependencies (verified by inspecting the installed dependency tree).
- **Demo clarity**: a first-time viewer of the README/GIF can explain what problem Adaptron solves within 30 seconds, without reading prose beyond the top of the page.

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Adapter registry doesn't scale to real-world type diversity | Ship a small but genuinely useful default adapter set (str/dict/common message types) and make custom registration a first-class, well-documented API |
| Duck-typed bridges break silently when LangChain/CrewAI change their internal APIs | Pin supported version ranges for each bridge and fail wrapping loudly with a clear error rather than wrapping incorrectly |
| Project reads as "yet another agent framework" in a crowded space (LangGraph, AutoGen, Semantic Kernel) | Keep messaging tightly scoped to interoperability, not orchestration — Adaptron connects agents built elsewhere, it doesn't replace those frameworks |
| Construction-time type errors feel too rigid for exploratory use | Consider a documented "best-effort" mode (future consideration, see §12) that warns instead of failing, without making it the default |
| Demo/playground overstates capability if it's simulated rather than live | Clearly label any simulated/mocked playground output as illustrative, and keep at least one real, runnable example in the repo |

## 10. Assumptions & Dependencies

- LangChain and CrewAI are the two initial framework bridges; both are assumed accessible via their public Python APIs.
- No LLM provider is required by Adaptron itself — it is agent-agnostic and does not make model calls on its own behalf.
- Single-process execution is sufficient for v1; no distributed runtime dependency is required.
- The project is primarily distributed via PyPI and GitHub, with no hosted backend required for the core library to function.

## 11. Milestones

1. Core agent/port abstraction — base `Agent` class, type declaration/inference, `wrap()` for plain Python callables only.
2. Pipeline + `>>` operator — construct and run linear pipelines of wrapped plain-Python agents, no adapters yet.
3. Adapter registry + auto-adaptation — `register_adapter`, type-mismatch detection at construction time, automatic insertion into the pipeline.
4. Logging/observability layer — verbose execution log showing agent and adapter stages.
5. LangChain bridge — optional module wrapping LangChain agents via duck typing.
6. CrewAI bridge — optional module wrapping CrewAI agents via duck typing.
7. Error handling polish — clear construction-time and run-time errors with actionable messages.
8. Example pipelines + README — a working example combining a real LangChain agent, a real CrewAI agent, and a plain Python function, plus a before/after code comparison for docs.
9. (Stretch) Interactive demo/playground — a simulated pipeline runner for a docs site showing the log output and adaptation visually, without requiring live LLM calls.

## 12. Future Considerations (Post-v1 Roadmap)

The items below are deliberately deferred, not unresolved blockers — v1 scope is fully decided by §3.3 (Non-goals) and §6 (Functional Requirements). These are candidate directions once the core library has shipped and proven itself:

- **Best-effort mode**: an opt-in `Pipeline(strict=False)` (or similar) that warns and passes raw data through on a type mismatch instead of failing at construction time, for exploratory/notebook use. Would remain opt-in — construction-time failure stays the default (§6.4).
- **Subclass/MRO-aware adapter resolution**: walking the type hierarchy instead of requiring an exact `(source_type, target_type)` pair, so an adapter registered for a base class also covers its subclasses (see the v1 limitation noted in §6.4).
- **Many-to-one adapter coercion**: allowing multiple compatible source types to map to one target type, rather than strictly one-to-one pairs.
- **Branching/parallel pipeline topology**: one agent's output feeding two or more downstream agents, once the linear-chain core (§3.3) is stable and there's real demand for it.
- **Native async execution**: an `arun()` counterpart to `run()` if enough real-world pipelines are bottlenecked on synchronous LLM calls.