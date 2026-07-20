# Adaptron playground (stretch)

**Status:** Tasks 9.1–9.3 done (format, mocked replay UI, README + changelog
link). Stretch playground is complete for v1 docs purposes.

## Open the replay

Open [`index.html`](./index.html) in a browser (double-click or a static file
server). Play / Step walks the scripted flagship stages; no Python or LLM
required.

| File | Role |
|---|---|
| [`index.html`](./index.html) | Page shell + **illustrative-only** banner |
| [`styles.css`](./styles.css) | Layout / diagram / log styling |
| [`replay.js`](./replay.js) | Sequential replay controls |
| [`replay-data.json`](./replay-data.json) | Scripted stage logs + final result |

## Decision: static site (not a notebook)

**Chosen format:** a small **static site** under this directory (HTML/CSS/JS,
optionally a tiny diagram + sequential log panel).

**Rejected for v1 stretch:** Jupyter notebook.

### Why static site

| Criterion | Static site | Notebook |
|---|---|---|
| Matches `PRD.md` §11 / `STRUCTURE.md` (“docs site”, diagram + log) | Yes | Weaker fit |
| No live LLM / no API keys (`PRD.md` §9) | Easy — scripted JSON/text only | Easy, but a kernel looks “runnable” |
| Risk of overstating capability | Lower — page is clearly a viewer | Higher — cells look like live code |
| Visitor friction (portfolio / README) | Open in browser / GitHub | Needs Jupyter or nbviewer |
| Extra dependencies for contributors | None beyond editing HTML/assets | Notebook tooling / CI noise |

The playground **replays** the Phase 8 flagship
([`examples/cross_framework_pipeline.py`](../../examples/cross_framework_pipeline.py))
with **pre-scripted** stage outputs and log lines. It does **not** call
`Pipeline.run()`, LangChain, CrewAI, or any LLM.

Real execution stays in the repo examples (`--mock` / `--live`).

## “Illustrative only” banner requirements

Every playground page and any embedded preview **must** include a persistent,
unmissable banner that states all of the following:

1. **Simulated / illustrative** — this is not a live Adaptron run.
2. **No LLM calls** — no API keys; outputs are scripted for docs.
3. **Pointer to the real demo** — link to
   `examples/cross_framework_pipeline.py` (and note `--mock` vs `--live`).

### Suggested banner copy

> **Illustrative simulation only.** This page replays a scripted walkthrough of
> the flagship pipeline. It does **not** execute Adaptron, LangChain, CrewAI,
> or any LLM. For a real run, see
> [`examples/cross_framework_pipeline.py`](../../examples/cross_framework_pipeline.py)
> (`--mock` needs no API keys; `--live` needs `OPENAI_API_KEY`).

### Placement rules (Task 9.2+)

- Banner visible **above the fold** on first paint (not only in a footer).
- Same wording (or stricter) on any shareable screenshot / GIF derived from
  the playground.
- Do not title the page “Live playground” or “Try it now” without the
  simulation qualifier in the same heading.

## Planned contents (Task 9.2) — shipped

- Scripted stages matching the flagship order: LangChain researcher →
  `adapter<Message->str>` → CrewAI writer → plain `format_result`.
- Visual: linear diagram of those stages (highlights as the replay advances).
- Sequential log UI mirroring `Pipeline.run(..., verbose=True)` line format.
- Final mocked result object (`status` / `draft` / `words`).

## Non-goals

- Hosting a backend or calling `wrap()` / `Pipeline.run()` from the page.
- Requiring `adaptron[langchain,crewai]` to view the playground.
- Replacing the runnable examples in `examples/`.
