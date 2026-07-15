"""Tests for Pipeline, ``>>`` flattening, and run() — Milestone 2 (PLAN.md §3)."""

from __future__ import annotations

import pytest
from adaptron import Pipeline, wrap
from adaptron.core.errors import PipelineExecutionError


def _to_str(n: int) -> str:
    return str(n)


def _exclaim(text: str) -> str:
    return text + "!"


def _length(text: str) -> int:
    return len(text)


def _boom(text: str) -> str:
    raise RuntimeError("kaboom")


def test_two_stage_pipeline_correct_output() -> None:
    pipeline = wrap(_to_str) >> wrap(_exclaim)
    assert isinstance(pipeline, Pipeline)
    assert pipeline.run(3) == "3!"


def test_three_stage_pipeline_correct_output() -> None:
    pipeline = wrap(_to_str) >> wrap(_exclaim) >> wrap(_length)
    assert pipeline.run(3) == len("3!")


def test_chained_rshift_is_single_flat_pipeline() -> None:
    a, b, c = wrap(_to_str), wrap(_exclaim), wrap(_length)
    pipeline = a >> b >> c
    assert isinstance(pipeline, Pipeline)
    assert pipeline.stages == [a, b, c]
    assert not any(isinstance(stage, Pipeline) for stage in pipeline.stages)


def test_nested_composition_equals_flat_chain() -> None:
    a, b, c = wrap(_to_str), wrap(_exclaim), wrap(_length)
    grouped = (a >> b) >> c
    flat = a >> b >> c
    assert grouped.stages == flat.stages == [a, b, c]

    other_grouping = a >> (b >> c)
    assert other_grouping.stages == flat.stages


def test_input_and_output_type_from_first_and_last_stage() -> None:
    pipeline = wrap(_to_str) >> wrap(_exclaim) >> wrap(_length)
    assert pipeline.input_type is int
    assert pipeline.output_type is int


def test_mid_pipeline_failure_raises_pipeline_execution_error() -> None:
    boom_agent = wrap(_boom)
    pipeline = wrap(_to_str) >> boom_agent

    with pytest.raises(PipelineExecutionError) as exc_info:
        pipeline.run(3)

    error = exc_info.value
    assert error.stage_name == boom_agent.name
    assert error.stage_input == "3"
    assert isinstance(error.__cause__, RuntimeError)
    assert boom_agent.name in str(error)


def test_pipeline_requires_at_least_one_stage() -> None:
    with pytest.raises(ValueError):
        Pipeline([])


def test_pipeline_rrshift_with_agent_on_left() -> None:
    a, b, c = wrap(_to_str), wrap(_exclaim), wrap(_length)
    pipeline_bc = b >> c
    result = a >> pipeline_bc
    assert result.stages == [a, b, c]
