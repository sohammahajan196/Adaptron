"""Tests for the CrewAI bridge — Milestone 6 (PLAN.md §3).

Gated on ``crewai`` being installed; runs in the CI bridge job
(`adaptron[crewai]` / ``adaptron[langchain,crewai]``), skipped entirely
in the core-only job.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("crewai")

from adaptron import wrap  # noqa: E402
from adaptron.bridges import crewai_bridge  # noqa: E402
from adaptron.core.agent import Agent  # noqa: E402


class _FakeAgentOutput:
    """Minimal stand-in for CrewAI ``LiteAgentOutput`` / ``CrewOutput``."""

    def __init__(self, raw: str) -> None:
        self.raw = raw


class _FakeCrewAIAgent:
    """Minimal duck-typed stand-in for a CrewAI ``Agent``."""

    role = "researcher"
    goal = "find answers"

    def kickoff(self, messages: Any) -> _FakeAgentOutput:
        text = messages if isinstance(messages, str) else str(messages)
        return _FakeAgentOutput(text.upper())


class _FakeCrew:
    """Minimal duck-typed stand-in for a CrewAI ``Crew``."""

    agents: list[Any] = []
    tasks: list[Any] = []

    def kickoff(self, inputs: dict[str, Any] | None = None) -> _FakeAgentOutput:
        return _FakeAgentOutput(str(inputs))


class _PlainCallable:
    """A plain callable — must never be routed through the CrewAI bridge."""

    def __call__(self, value: str) -> str:
        return value


def test_can_wrap_true_for_agent_and_crew() -> None:
    assert crewai_bridge.can_wrap(_FakeCrewAIAgent()) is True
    assert crewai_bridge.can_wrap(_FakeCrew()) is True


def test_can_wrap_false_for_plain_callable() -> None:
    assert crewai_bridge.can_wrap(_PlainCallable()) is False


def test_adapt_delegates_to_kickoff_with_default_str_types() -> None:
    agent = crewai_bridge.adapt(_FakeCrewAIAgent())
    assert isinstance(agent, Agent)
    assert agent.input_type is str
    assert agent.output_type is str
    assert agent.name == "_FakeCrewAIAgent"
    assert agent("hi") == "HI"


def test_adapt_delegates_to_crew_kickoff_with_inputs() -> None:
    agent = crewai_bridge.adapt(_FakeCrew())
    assert agent("topic") == str({"input": "topic"})
    assert agent({"topic": "AI"}) == str({"topic": "AI"})


def test_wrap_uses_bridge_for_agent_like_object() -> None:
    agent = wrap(_FakeCrewAIAgent())
    assert isinstance(agent, Agent)
    assert agent.input_type is str
    assert agent.output_type is str
    assert agent("adaptron") == "ADAPTRON"


def test_wrap_uses_bridge_for_crew_like_object() -> None:
    agent = wrap(_FakeCrew())
    assert agent("adaptron") == str({"input": "adaptron"})


def test_wrap_respects_explicit_overrides_through_bridge() -> None:
    agent = wrap(_FakeCrewAIAgent(), name="custom")
    assert agent.name == "custom"


def test_regression_crewai_duck_type_not_mis_wrapped_as_plain_callable() -> None:
    """An Agent-like object has no ``__call__``: the plain-Python path
    alone would raise ``WrapError`` ("not callable"). Successfully
    wrapping it here proves the CrewAI bridge — not the catch-all —
    handled it (PLAN.md §2.4 probe order).
    """
    obj = _FakeCrewAIAgent()
    assert not callable(obj)

    agent = wrap(obj)
    assert agent("adaptron") == "ADAPTRON"


def test_plain_callable_still_wraps_normally() -> None:
    agent = wrap(_PlainCallable())
    assert agent.name == "_PlainCallable"
    assert agent("same") == "same"
