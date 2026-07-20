"""Tests for post-v1 backlog features (best-effort, MRO, parallel, arun)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from adaptron import Pipeline, parallel, register_adapter, wrap
from adaptron.core import adapters as adapters_module
from adaptron.core.errors import AdaptronError, NoAdapterError


@pytest.fixture(autouse=True)
def _isolated_registry() -> Any:
    original = dict(adapters_module._registry)
    yield
    adapters_module._registry.clear()
    adapters_module._registry.update(original)


class _Base:
    pass


class _Child(_Base):
    def __init__(self, n: int) -> None:
        self.n = n


def test_best_effort_skips_missing_adapter_with_warning() -> None:
    def produce(x: str) -> _Child:
        return _Child(1)

    def consume(y: dict) -> str:  # type: ignore[type-arg]
        return type(y).__name__

    with pytest.raises(NoAdapterError):
        Pipeline([wrap(produce), wrap(consume, input_type=dict)])

    with pytest.warns(UserWarning, match="best-effort"):
        pipeline = Pipeline(
            [wrap(produce), wrap(consume, input_type=dict)],
            strict=False,
        )

    assert pipeline.run("hi") == "_Child"


def test_mro_many_to_one_base_adapter_serves_subclass() -> None:
    def produce(x: str) -> _Child:
        return _Child(7)

    def consume(b: _Base) -> int:
        assert isinstance(b, _Child)
        return b.n

    register_adapter(_Base, _Base, lambda b: b)

    with pytest.raises(NoAdapterError):
        Pipeline([wrap(produce), wrap(consume)])

    pipeline = Pipeline([wrap(produce), wrap(consume)], resolve_mro=True)
    assert any(s.name.startswith("adapter<") for s in pipeline.stages)
    assert pipeline.run("x") == 7


def test_parallel_fan_out_returns_tuple() -> None:
    def double(n: int) -> int:
        return n * 2

    def square(n: int) -> int:
        return n * n

    stage = parallel(wrap(double), wrap(square), name="fan")
    assert stage(3) == (6, 9)

    def sum_pair(pair: tuple) -> int:  # type: ignore[type-arg]
        return int(pair[0]) + int(pair[1])

    pipeline = stage >> wrap(sum_pair)
    assert pipeline.run(3) == 15


def test_arun_awaits_async_agent() -> None:
    async def aupper(text: str) -> str:
        return text.upper()

    def exclaim(text: str) -> str:
        return text + "!"

    pipeline = wrap(aupper) >> wrap(exclaim)
    with pytest.raises(AdaptronError, match="arun"):
        pipeline.run("hi")

    assert asyncio.run(pipeline.arun("hi")) == "HI!"


def test_empty_parallel_raises() -> None:
    with pytest.raises(AdaptronError, match="parallel"):
        parallel()
