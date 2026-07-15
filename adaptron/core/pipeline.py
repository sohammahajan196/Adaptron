"""Pipeline — linear composition of Agents via ``>>`` (PLAN.md §2.2).

Usage::

    pipeline = wrap(agent_a) >> wrap(agent_b) >> wrap(agent_c)
    result = pipeline.run(input_value)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union

from adaptron.core.adapters import get_adapter
from adaptron.core.agent import Agent
from adaptron.core.errors import NoAdapterError, PipelineExecutionError
from adaptron.core.logging import log_stage

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


def _type_name(tp: Any) -> str:
    """Return a short display name for a type, used in adapter stage names."""
    if tp is Any:
        return "Any"
    name = getattr(tp, "__name__", None)
    return name if isinstance(name, str) else repr(tp)


def _resolve_adjacent(left: Agent, right: Agent) -> list[Agent]:
    """Resolve compatibility between two adjacent stages (PLAN.md §2.3).

    Returns the adapter stage to insert between ``left`` and ``right`` as a
    single-element list, or an empty list if none is needed:

    - Exact type match, or ``Any`` on either side, is treated as compatible
      and needs no adapter (``Any`` skips resolution entirely, per PRD §6.2).
    - Otherwise, an exact ``(source_type, target_type)`` adapter must be
      registered (``register_adapter``); it is wrapped in its own named
      ``Agent`` stage so it is visible in logs later (Phase 4).
    - If no such adapter is registered, raises ``NoAdapterError``
      immediately — construction time, never deferred to ``run()``.
    """
    source_type = left.output_type
    target_type = right.input_type

    if source_type is target_type or source_type is Any or target_type is Any:
        return []

    adapter_fn = get_adapter(source_type, target_type)
    if adapter_fn is None:
        raise NoAdapterError(source_type, target_type)

    adapter_name = f"adapter<{_type_name(source_type)}->{_type_name(target_type)}>"
    adapter_stage = Agent(
        adapter_fn,
        input_type=source_type,
        output_type=target_type,
        name=adapter_name,
    )
    return [adapter_stage]


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

    Adjacent-stage compatibility is resolved at construction time
    (PLAN.md §2.3): an exact type match, or ``Any`` on either side, needs
    no adapter; a registered ``(source_type, target_type)`` adapter is
    inserted as its own stage; an unresolved mismatch raises
    ``NoAdapterError`` immediately — never deferred to ``run()``.

    Attributes:
        stages: The ordered, flat list of ``Agent`` stages to run in
            sequence (including any inserted adapter stages). Must contain
            at least one stage.
    """

    stages: list[Agent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.stages:
            raise ValueError("Pipeline requires at least one stage.")
        resolved: list[Agent] = [self.stages[0]]
        for left, right in zip(self.stages, self.stages[1:], strict=False):
            resolved.extend(_resolve_adjacent(left, right))
            resolved.append(right)
        self.stages = resolved

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

    def run(self, value: Any, *, verbose: bool = False) -> Any:
        """Execute all stages in order, threading each output into the next.

        Silent by default: no log records or handler noise unless the
        caller opts in with ``verbose=True``. Verbosity never changes the
        computed output (PRD §6.5, PLAN.md §3 Milestone 4).

        Args:
            value: The input to the first stage.
            verbose: If ``True``, emit one INFO record per stage (agent or
                inserted adapter, in execution order) via the ``adaptron``
                logger (``core/logging.py``), naming the stage, its
                input/output types, and truncated input/output previews.

        Returns:
            The output of the last stage.

        Raises:
            PipelineExecutionError: If a stage raises while processing its
                input. Carries that stage's name and the input it received
                (PRD §6.6); the original exception is preserved as
                ``__cause__``.
        """
        for stage in self.stages:
            stage_input = value
            try:
                value = stage(value)
            except Exception as exc:
                raise PipelineExecutionError(stage.name, value) from exc
            if verbose:
                log_stage(
                    stage.name,
                    stage.input_type,
                    stage.output_type,
                    stage_input,
                    value,
                )
        return value
