"""Tests for actionable error messages — Milestone 7 (PLAN.md §3 / PRD §6.6)."""

from __future__ import annotations

from typing import Any

import pytest
from adaptron import register_adapter, wrap
from adaptron.core import adapters as adapters_module
from adaptron.core.errors import (
    AdaptronError,
    NoAdapterError,
    PipelineExecutionError,
    WrapError,
)


@pytest.fixture(autouse=True)
def _isolated_registry() -> Any:
    """Snapshot/restore the global adapter registry so tests don't leak state."""
    original = dict(adapters_module._registry)
    yield
    adapters_module._registry.clear()
    adapters_module._registry.update(original)


class _Src:
    pass


class _Tgt:
    pass


def test_wrap_error_message_names_type_and_fix() -> None:
    with pytest.raises(WrapError) as exc_info:
        wrap(42)

    message = str(exc_info.value)
    assert isinstance(exc_info.value, AdaptronError)
    assert "not callable" in message
    assert "int" in message
    assert "function" in message.lower() or "__call__" in message


def test_wrap_error_message_for_bare_class() -> None:
    with pytest.raises(WrapError) as exc_info:
        wrap(_Src)

    message = str(exc_info.value)
    assert "_Src" in message
    assert "class" in message.lower()
    assert "instance" in message.lower()


def test_no_adapter_error_message_suggests_register_adapter() -> None:
    def produce(x: str) -> _Src:
        return _Src()

    def consume(y: _Tgt) -> str:
        return "unused"

    with pytest.raises(NoAdapterError) as exc_info:
        wrap(produce) >> wrap(consume)

    error = exc_info.value
    message = str(error)
    assert error.source_type is _Src
    assert error.target_type is _Tgt
    assert "_Src -> _Tgt" in message
    assert "register_adapter(_Src, _Tgt, fn)" in message


def test_pipeline_execution_error_message_names_stage_and_input() -> None:
    def to_upper(text: str) -> str:
        return text.upper()

    def boom(text: str) -> str:
        raise RuntimeError("kaboom")

    boom_agent = wrap(boom)
    pipeline = wrap(to_upper) >> boom_agent

    with pytest.raises(PipelineExecutionError) as exc_info:
        pipeline.run("hi")

    error = exc_info.value
    message = str(error)
    assert error.stage_name == boom_agent.name
    assert error.stage_input == "HI"
    assert error.source_type is None
    assert error.target_type is None
    assert boom_agent.name in message
    assert "'HI'" in message or '"HI"' in message
    assert isinstance(error.__cause__, RuntimeError)


def test_adapter_failure_message_includes_types_stage_and_input() -> None:
    def produce(text: str) -> str:
        return text.upper()

    def boom_adapter(text: str) -> dict[str, str]:
        raise ValueError("bad convert")

    seen: list[Any] = []

    def consume(d: dict[str, str]) -> int:
        seen.append(d)
        return 0

    with pytest.warns(UserWarning, match="str -> dict"):
        register_adapter(str, dict, boom_adapter)

    pipeline = wrap(produce) >> wrap(consume, input_type=dict)
    assert any(s.name.startswith("adapter<") for s in pipeline.stages)

    with pytest.raises(PipelineExecutionError) as exc_info:
        pipeline.run("hi")

    error = exc_info.value
    message = str(error)
    assert error.stage_name == "adapter<str->dict>"
    assert error.stage_input == "HI"
    assert error.source_type is str
    assert error.target_type is dict
    assert "Adapter stage" in message
    assert "str -> dict" in message
    assert "register_adapter(str, dict, fn)" in message
    assert "'HI'" in message or '"HI"' in message
    assert isinstance(error.__cause__, ValueError)
    assert seen == []
