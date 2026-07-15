"""Tests for Agent and wrap() — Milestone 1 (PLAN.md §3)."""

from __future__ import annotations

from typing import Any

import pytest
from adaptron import Agent, wrap
from adaptron.core.errors import WrapError


def _typed_upper(text: str) -> str:
    return text.upper()


def _untyped(value):  # type: ignore[no-untyped-def]
    return value


class _Multiplier:
    def __call__(self, n: int) -> int:
        return n * 2


def test_typed_function_inference() -> None:
    agent = wrap(_typed_upper)
    assert isinstance(agent, Agent)
    assert agent.input_type is str
    assert agent.output_type is str
    assert agent.name == "_typed_upper"
    assert agent("hello") == "HELLO"


def test_untyped_function_falls_back_to_any() -> None:
    agent = wrap(_untyped)
    assert agent.input_type is Any
    assert agent.output_type is Any
    assert agent(42) == 42


def test_callable_class_instance() -> None:
    agent = wrap(_Multiplier())
    assert agent.input_type is int
    assert agent.output_type is int
    assert agent.name == "_Multiplier"
    assert agent(3) == 6


def test_wrap_error_on_non_callable() -> None:
    with pytest.raises(WrapError, match="not callable") as exc_info:
        wrap(42)
    message = str(exc_info.value)
    assert "int" in message
    assert "function" in message.lower() or "__call__" in message


def test_wrap_error_on_bare_class() -> None:
    with pytest.raises(WrapError, match="class") as exc_info:
        wrap(_Multiplier)
    message = str(exc_info.value)
    assert "_Multiplier" in message
    assert "instance" in message.lower()


def test_explicit_type_override_wins_over_hints() -> None:
    agent = wrap(
        _typed_upper,
        input_type=bytes,
        output_type=list,
        name="overridden",
    )
    assert agent.input_type is bytes
    assert agent.output_type is list
    assert agent.name == "overridden"
