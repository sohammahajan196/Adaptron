"""Pipeline — linear composition of Agents via ``>>`` (PLAN.md §2.2).

Usage::

    pipeline = wrap(agent_a) >> wrap(agent_b) >> wrap(agent_c)
    result = pipeline.run(input_value)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union

from adaptron.core.agent import Agent
from adaptron.core.errors import PipelineExecutionError

PipelineStage = Union[Agent, "Pipeline"]


def _flatten(stage: PipelineStage) -> list[Agent]:
    """Expand a stage into a flat list of ``Agent``\\ s.

    A ``Pipeline`` contributes its own stage list (never itself, so chains
    never nest ``Pipeline``-in-``Pipeline``); an ``Agent`` contributes
    itself as a single-element list.
    """
    if isinstance(stage, Pipeline):
        return list(stage.stages)
    return [stage]


def _check_adjacent_compatible(left: Agent, right: Agent) -> None:
    """Stubbed construction-time compatibility check (PLAN.md §2.2/§2.3).

    Always treats adjacent stages as compatible and never inserts an
    adapter. Phase 3 replaces this with real adapter-registry resolution:
    exact type match or ``Any`` passes through, a registered adapter is
    inserted as an extra stage, and an unregistered mismatch raises
    ``NoAdapterError`` at construction time (not at ``run()``).
    """
    return None


@dataclass
class Pipeline:
    """A linear, ordered sequence of ``Agent`` stages built with ``>>``.

    ``a >> b`` (via ``Agent.__rshift__``/``__rrshift__``) returns a
    ``Pipeline`` containing ``[a, b]``. Chaining further (``a >> b >> c``)
    flattens into one ``Pipeline`` with three stages rather than nesting
    pipelines, and this holds regardless of grouping — ``(a >> b) >> c``
    produces the same flat three-stage ``Pipeline`` as ``a >> b >> c``.

    Composability: a ``Pipeline`` exposes ``.input_type``/``.output_type``
    (from its first/last stage), the same public shape as ``Agent``. This
    lets a fully-built ``Pipeline`` be used as either side of ``>>`` like
    any other stage.

    No adapter resolution happens yet in this milestone — adjacent-stage
    compatibility is a no-op stub (``_check_adjacent_compatible``); every
    pair of stages is treated as compatible pending Phase 3.

    Attributes:
        stages: The ordered, flat list of ``Agent`` stages to run in
            sequence. Must contain at least one stage.
    """

    stages: list[Agent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.stages:
            raise ValueError("Pipeline requires at least one stage.")
        for left, right in zip(self.stages, self.stages[1:], strict=False):
            _check_adjacent_compatible(left, right)

    @property
    def input_type(self) -> Any:
        """The input type of the first stage."""
        return self.stages[0].input_type

    @property
    def output_type(self) -> Any:
        """The output type of the last stage."""
        return self.stages[-1].output_type

    def __rshift__(self, other: PipelineStage) -> Pipeline:
        """Chain ``other`` after this pipeline, flattening nested stages."""
        if not isinstance(other, (Agent, Pipeline)):
            return NotImplemented
        return Pipeline([*self.stages, *_flatten(other)])

    def __rrshift__(self, other: PipelineStage) -> Pipeline:
        """Chain this pipeline after ``other``, flattening nested stages."""
        if not isinstance(other, (Agent, Pipeline)):
            return NotImplemented
        return Pipeline([*_flatten(other), *self.stages])

    def run(self, value: Any) -> Any:
        """Execute all stages in order, threading each output into the next.

        No logging happens yet — this milestone runs silently by default;
        verbose per-stage logging arrives in Phase 4 (``core/logging.py``).

        Args:
            value: The input to the first stage.

        Returns:
            The output of the last stage.

        Raises:
            PipelineExecutionError: If a stage raises while processing its
                input. Carries that stage's name and the input it received
                (PRD §6.6); the original exception is preserved as
                ``__cause__``.
        """
        for stage in self.stages:
            try:
                value = stage(value)
            except Exception as exc:
                raise PipelineExecutionError(stage.name, value) from exc
        return value
