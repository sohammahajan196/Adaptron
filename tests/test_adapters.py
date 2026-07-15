"""Tests for the adapter registry and construction-time resolution — Milestone 3."""

from __future__ import annotations

from typing import Any

import pytest
from adaptron import Pipeline, register_adapter, wrap
from adaptron.core import adapters as adapters_module
from adaptron.core.errors import NoAdapterError


@pytest.fixture(autouse=True)
def _isolated_registry() -> Any:
    """Snapshot/restore the global adapter registry so tests don't leak state."""
    original = dict(adapters_module._registry)
    yield
    adapters_module._registry.clear()
    adapters_module._registry.update(original)


class _Foo:
    """Module-level (not local) so ``get_type_hints`` can resolve it."""


class _Bar:
    """Module-level (not local) so ``get_type_hints`` can resolve it."""


def _produce_int(n: int) -> str:
    return str(n)


def _produce_foo(x: str) -> _Foo:
    return _Foo()


def _consume_bar(b: _Bar) -> str:
    return "unreachable"


def test_registered_mismatch_auto_inserts_and_run_succeeds() -> None:
    def consume_dict(d: dict[str, str]) -> int:
        return len(d["text"])

    # Explicit input_type=dict: the default adapter is registered for the
    # bare `dict` type, not the parameterized `dict[str, str]` alias — v1
    # resolution is exact-pair only (PLAN.md §2.3), so this pins the port
    # type this test means to exercise.
    pipeline = wrap(_produce_int) >> wrap(consume_dict, input_type=dict)

    assert len(pipeline.stages) == 3
    assert pipeline.stages[1].name == "adapter<str->dict>"
    assert pipeline.run(42) == len("42")


def test_unregistered_mismatch_raises_at_construction_not_run() -> None:
    with pytest.raises(NoAdapterError, match="register_adapter") as exc_info:
        wrap(_produce_foo) >> wrap(_consume_bar)

    error = exc_info.value
    assert error.source_type is _Foo
    assert error.target_type is _Bar


def test_reregistration_emits_warning() -> None:
    class Widget:
        pass

    def to_widget_v1(s: str) -> Widget:
        return Widget()

    def to_widget_v2(s: str) -> Widget:
        return Widget()

    register_adapter(str, Widget, to_widget_v1)

    with pytest.warns(UserWarning, match="str -> Widget"):
        register_adapter(str, Widget, to_widget_v2)


def test_any_skips_resolution() -> None:
    def produce_any(x: str) -> Any:
        return x

    def consume_any(x: Any) -> int:
        return len(x)

    def produce_str(x: int) -> str:
        return str(x)

    def consume_str_as_any(x: str) -> Any:
        return x

    output_any_pipeline = wrap(produce_any) >> wrap(consume_any)
    assert isinstance(output_any_pipeline, Pipeline)
    assert len(output_any_pipeline.stages) == 2

    input_any_pipeline = wrap(produce_str) >> wrap(consume_str_as_any)
    assert isinstance(input_any_pipeline, Pipeline)
    assert len(input_any_pipeline.stages) == 2
