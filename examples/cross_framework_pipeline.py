"""Flagship cross-framework pipeline (LangChain → CrewAI → plain Python).

Demonstrates Adaptron auto-adaptation across frameworks: a LangChain-shaped
researcher emits a ``Message``, a registered ``Message → str`` adapter
converts it, a CrewAI-shaped writer consumes the string, and a plain
Python formatter finishes the pipeline.

---------------------------------------------------------------------------
Install (required in both modes — bridges lazy-import the packages)::

    pip install -e ".[langchain,crewai]"

Environment variables
---------------------
OPENAI_API_KEY
    Required only for ``--live``. Used by LangChain ChatOpenAI and CrewAI's
    default LLM. Never required for the default ``--mock`` mode.

ADAPTRON_EXAMPLE_MODE
    Optional. Set to ``live`` to default to live agents (same as ``--live``).
    Set to ``mock`` (default) for duck-typed stand-ins.

Modes
-----
``--mock`` (default)
    **ILLUSTRATIVE / MOCKED for demos and CI.** Duck-typed stand-ins that
    satisfy LangChain Runnable and CrewAI Agent shapes so ``wrap()`` uses
    the real bridges — but **no LLM API calls** are made. Safe without keys.

``--live``
    Attempts real LangChain (ChatOpenAI) + CrewAI ``Agent.kickoff`` agents.
    Needs ``OPENAI_API_KEY`` and typically ``pip install langchain-openai``.
    Falls back with a clear error if the live stack is unavailable.

Run::

    python examples/cross_framework_pipeline.py --verbose
    python examples/cross_framework_pipeline.py --live --verbose
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Iterator
from typing import Any

from adaptron import Pipeline, register_adapter, wrap
from adaptron.core.adapters import Message, get_adapter

# ---------------------------------------------------------------------------
# Shared plain-Python formatter (always real — never mocked)
# ---------------------------------------------------------------------------


def format_result(draft: str) -> dict[str, str]:
    """Turn the CrewAI draft string into a small result dict."""
    return {
        "status": "ok",
        "draft": draft,
        "words": str(len(draft.split())),
    }


def _message_to_str(message: Message) -> str:
    """Adapter: ``Message → str`` (genuine type mismatch for the demo)."""
    return message.text


def _require_bridge_extras() -> None:
    """Fail fast with install guidance if LangChain / CrewAI are absent."""
    missing: list[str] = []
    try:
        import langchain  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        missing.append("langchain")
    try:
        import crewai  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        missing.append("crewai")
    if missing:
        names = ", ".join(missing)
        raise SystemExit(
            f"Missing optional package(s): {names}. "
            'Install with: pip install -e ".[langchain,crewai]"'
        )


# ---------------------------------------------------------------------------
# MOCK mode — clearly labeled illustrative stand-ins (no LLM calls)
# ---------------------------------------------------------------------------


class _MockLangChainResearcher:
    """Duck-typed LangChain ``Runnable`` stand-in.

    **MOCKED / ILLUSTRATIVE** — exercises the LangChain bridge without an LLM.
    """

    def invoke(self, value: str) -> Message:
        return Message(text=f"[LC mock research] {value.strip()}")

    def batch(self, values: list[str]) -> list[Message]:
        return [self.invoke(v) for v in values]

    def stream(self, value: str) -> Iterator[Message]:
        yield self.invoke(value)


class _MockCrewAIWriterOutput:
    raw: str

    def __init__(self, raw: str) -> None:
        self.raw = raw


class _MockCrewAIWriter:
    """Duck-typed CrewAI ``Agent`` stand-in.

    **MOCKED / ILLUSTRATIVE** — exercises the CrewAI bridge without an LLM.
    """

    role = "editorial writer"
    goal = "turn research notes into a short draft"

    def kickoff(self, messages: Any) -> _MockCrewAIWriterOutput:
        text = messages if isinstance(messages, str) else str(messages)
        return _MockCrewAIWriterOutput(f"[CrewAI mock draft] {text}")


def build_mock_agents() -> tuple[Any, Any]:
    """Return (langchain-shaped, crewai-shaped) mocked agents."""
    return _MockLangChainResearcher(), _MockCrewAIWriter()


# ---------------------------------------------------------------------------
# LIVE mode — real framework agents (needs API key + extras)
# ---------------------------------------------------------------------------


def build_live_agents() -> tuple[Any, Any]:
    """Build a real LangChain runnable and CrewAI Agent.

    Raises:
        SystemExit: If keys or live dependencies are missing.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "Live mode requires OPENAI_API_KEY in the environment. "
            "Export it, or use --mock (default) for the illustrative demo."
        )

    try:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.runnables import RunnableLambda
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise SystemExit(
            "Live LangChain path needs langchain-openai / langchain-core. "
            'Try: pip install -e ".[langchain,crewai]" langchain-openai\n'
            f"Original import error: {exc}"
        ) from exc

    try:
        from crewai import Agent as CrewAgent
    except ImportError as exc:
        raise SystemExit(
            "Live CrewAI path needs the crewai package. "
            'Install with: pip install -e ".[crewai]"\n'
            f"Original import error: {exc}"
        ) from exc

    prompt = ChatPromptTemplate.from_template(
        "In one short sentence, research notes for: {topic}"
    )
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

    def _as_topic(topic: str) -> dict[str, str]:
        return {"topic": topic}

    # Runnable that yields adaptron Message so the Message→str adapter runs.
    lc_chain = (
        RunnableLambda(_as_topic)
        | prompt
        | model
        | StrOutputParser()
        | RunnableLambda(lambda text: Message(text=str(text)))
    )

    crew_agent = CrewAgent(
        role="editorial writer",
        goal="Turn research notes into one polished draft sentence",
        backstory="You write concise drafts from research notes.",
        allow_delegation=False,
        verbose=False,
    )
    return lc_chain, crew_agent


# ---------------------------------------------------------------------------
# Pipeline assembly
# ---------------------------------------------------------------------------


def build_pipeline(*, live: bool = False) -> Pipeline:
    """Build LangChain → (Message→str adapter) → CrewAI → plain formatter.

    Args:
        live: If ``True``, use real framework agents; otherwise mocked
            duck-typed stand-ins (default, safe for CI / no API keys).
    """
    _require_bridge_extras()
    if get_adapter(Message, str) is None:
        register_adapter(Message, str, _message_to_str)

    if live:
        lc_agent, crew_agent = build_live_agents()
    else:
        lc_agent, crew_agent = build_mock_agents()

    # Explicit ports so construction inserts adapter<Message->str>.
    return (
        wrap(
            lc_agent,
            input_type=str,
            output_type=Message,
            name="langchain_researcher",
        )
        >> wrap(
            crew_agent,
            input_type=str,
            output_type=str,
            name="crewai_writer",
        )
        >> wrap(format_result, name="format_result")
    )


def main(argv: list[str] | None = None) -> int:
    env_mode = os.environ.get("ADAPTRON_EXAMPLE_MODE", "mock").strip().lower()
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--mock",
        action="store_true",
        help="Use mocked LC/CrewAI stand-ins (default; no API calls)",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="Use real LangChain + CrewAI agents (needs OPENAI_API_KEY)",
    )
    parser.add_argument(
        "topic",
        nargs="?",
        default="adaptron interoperability",
        help="Input topic string (default: %(default)r)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log each agent and adapter stage (shows auto-adaptation)",
    )
    args = parser.parse_args(argv)

    live = args.live or (env_mode == "live" and not args.mock)
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    mode_label = "LIVE" if live else "MOCK (illustrative - no LLM calls)"
    print(f"mode={mode_label}", file=sys.stderr)

    pipeline = build_pipeline(live=live)
    adapter_stages = [s.name for s in pipeline.stages if s.name.startswith("adapter<")]
    if not adapter_stages:
        raise SystemExit("Expected at least one auto-inserted adapter stage.")
    print(f"auto_adapters={adapter_stages}", file=sys.stderr)

    result = pipeline.run(args.topic, verbose=args.verbose)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
