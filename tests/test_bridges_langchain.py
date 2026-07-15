"""Tests for the LangChain bridge — Milestone 5 (PLAN.md §3).

Gated on ``langchain`` being installed; runs in the CI bridge job
(`adaptron[langchain]`), skipped entirely in the core-only job.
"""

from __future__ import annotations

import pytest

pytest.importorskip("langchain")

from adaptron import wrap  # noqa: E402
from adaptron.bridges import langchain_bridge  # noqa: E402
from adaptron.core.agent import Agent  # noqa: E402


class _FakeRunnable:
    """Minimal duck-typed stand-in for a LangChain ``Runnable``."""

    def invoke(self, value: str) -> str:
        return value.upper()

    def batch(self, values: list[str]) -> list[str]:
        return [v.upper() for v in values]

    def stream(self, value: str):  # type: ignore[no-untyped-def]
        yield value.upper()


class _FakeLegacyChain:
    """Minimal duck-typed stand-in for a legacy LangChain ``Chain``."""

    input_keys = ["input"]
    output_keys = ["output"]

    def run(self, value: str) -> str:
        return value + "!"


class _PlainCallable:
    """A plain callable — must never be routed through the LangChain bridge."""

    def __call__(self, value: str) -> str:
        return value


def test_can_wrap_true_for_runnable_and_legacy_chain() -> None:
    assert langchain_bridge.can_wrap(_FakeRunnable()) is True
    assert langchain_bridge.can_wrap(_FakeLegacyChain()) is True


def test_can_wrap_false_for_plain_callable() -> None:
    assert langchain_bridge.can_wrap(_PlainCallable()) is False


def test_adapt_delegates_to_invoke_with_default_str_types() -> None:
    agent = langchain_bridge.adapt(_FakeRunnable())
    assert isinstance(agent, Agent)
    assert agent.input_type is str
    assert agent.output_type is str
    assert agent.name == "_FakeRunnable"
    assert agent("hi") == "HI"


def test_adapt_delegates_to_run_for_legacy_chain() -> None:
    agent = langchain_bridge.adapt(_FakeLegacyChain())
    assert agent("hi") == "hi!"


def test_wrap_uses_bridge_for_runnable_like_object() -> None:
    agent = wrap(_FakeRunnable())
    assert isinstance(agent, Agent)
    assert agent.input_type is str
    assert agent.output_type is str
    assert agent("adaptron") == "ADAPTRON"


def test_wrap_uses_bridge_for_legacy_chain_like_object() -> None:
    agent = wrap(_FakeLegacyChain())
    assert agent("adaptron") == "adaptron!"


def test_wrap_respects_explicit_overrides_through_bridge() -> None:
    agent = wrap(_FakeRunnable(), name="custom")
    assert agent.name == "custom"


def test_regression_langchain_duck_type_not_mis_wrapped_as_plain_callable() -> None:
    """A Runnable-like object has no ``__call__``: the plain-Python path
    alone would raise ``WrapError`` ("not callable"). Successfully
    wrapping it here proves the LangChain bridge — not the catch-all —
    handled it (PLAN.md §2.4 probe order).
    """
    obj = _FakeRunnable()
    assert not callable(obj)

    agent = wrap(obj)
    assert agent("adaptron") == "ADAPTRON"


def test_plain_callable_still_wraps_normally() -> None:
    agent = wrap(_PlainCallable())
    assert agent.name == "_PlainCallable"
    assert agent("same") == "same"
