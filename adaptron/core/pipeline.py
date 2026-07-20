"""Pipeline — composition of Agents via ``>>`` (PLAN.md §2.2).

Usage::

    pipeline = wrap(agent_a) >> wrap(agent_b) >> wrap(agent_c)
    result = pipeline.run(input_value)
"""

from __future__ import annotations

import inspect
import warnings
from dataclasses import dataclass, field
from typing import Any, Union

from adaptron.core.adapters import get_adapter
from adaptron.core.agent import Agent
from adaptron.core.errors import AdaptronError, NoAdapterError, PipelineExecutionError
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


def _is_adapter_stage(stage: Agent) -> bool:
    """Return ``True`` if ``stage`` was inserted by adapter resolution."""
    return stage.name.startswith("adapter<")


def _resolve_adjacent(
    left: Agent,
    right: Agent,
    *,
    strict: bool,
    resolve_mro: bool,
) -> list[Agent]:
    """Resolve compatibility between two adjacent stages (PLAN.md §2.3).

    Returns the adapter stage to insert between ``left`` and ``right`` as a
    single-element list, or an empty list if none is needed.
    """
    source_type = left.output_type
    target_type = right.input_type

    if source_type is target_type or source_type is Any or target_type is Any:
        return []

    adapter_fn = get_adapter(source_type, target_type, mro=resolve_mro)
    if adapter_fn is None:
        if strict:
            raise NoAdapterError(source_type, target_type)
        warnings.warn(
            f"best-effort pipeline: no adapter for "
            f"{_type_name(source_type)} -> {_type_name(target_type)}; "
            "passing value through unchecked. Register one with: "
            f"register_adapter({_type_name(source_type)}, "
            f"{_type_name(target_type)}, fn)",
            UserWarning,
            stacklevel=3,
        )
        return []

    adapter_name = f"adapter<{_type_name(source_type)}->{_type_name(target_type)}>"
    adapter_stage = Agent(
        adapter_fn,
        input_type=source_type,
        output_type=target_type,
        name=adapter_name,
    )
    return [adapter_stage]


def parallel(*agents: Agent, name: str = "parallel") -> Agent:
    """Run several agents on the same input and return a ``tuple`` of outputs.

    Post-v1 branching helper: fans out one value to each agent (in order),
    collects results into a tuple. Does not run true OS threads — execution
    is still synchronous and sequential unless used inside ``arun`` with
    async agents (each branch is still awaited in order).

    Args:
        *agents: One or more ``Agent`` stages (not nested pipelines).
        name: Stage name for logs/errors.

    Returns:
        An ``Agent`` whose output type is ``tuple``.
    """
    if not agents:
        raise AdaptronError(
            "parallel() requires at least one Agent. "
            "Example: parallel(wrap(a), wrap(b)) >> wrap(merge_fn)."
        )
    if not all(isinstance(a, Agent) for a in agents):
        raise AdaptronError(
            "parallel() only accepts Agent instances. Wrap callables with wrap() first."
        )

    branches: tuple[Agent, ...] = agents

    def _call(value: Any) -> tuple[Any, ...]:
        return tuple(branch(value) for branch in branches)

    # Prefer a shared input type when all branches agree; else Any.
    in_types = {b.input_type for b in branches}
    input_type: Any = next(iter(in_types)) if len(in_types) == 1 else Any

    return Agent(_call, input_type=input_type, output_type=tuple, name=name)


@dataclass
class Pipeline:
    """A linear, ordered sequence of ``Agent`` stages built with ``>>``.

    ``a >> b`` returns a ``Pipeline`` containing ``[a, b]``. Chaining further
    flattens into one ``Pipeline``. Optional post-v1 flags:

    - ``strict=False``: missing adapters warn and pass through (best-effort).
      Default ``strict=True`` still raises ``NoAdapterError``.
    - ``resolve_mro=True``: adapter lookup may use base-class registrations
      (subclass / many-to-one coercion). Default remains exact-pair only.

    Attributes:
        stages: Ordered flat ``Agent`` list (including inserted adapters).
        strict: Construction-time adapter required (default ``True``).
        resolve_mro: Enable MRO-aware adapter lookup (default ``False``).
    """

    stages: list[Agent] = field(default_factory=list)
    strict: bool = True
    resolve_mro: bool = False

    def __post_init__(self) -> None:
        if not self.stages:
            raise AdaptronError(
                "Pipeline requires at least one stage. Build one with "
                "wrap(a) >> wrap(b), or pass a non-empty list of Agent stages "
                "to Pipeline(...)."
            )
        resolved: list[Agent] = [self.stages[0]]
        for left, right in zip(self.stages, self.stages[1:], strict=False):
            resolved.extend(
                _resolve_adjacent(
                    left,
                    right,
                    strict=self.strict,
                    resolve_mro=self.resolve_mro,
                )
            )
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
        return Pipeline(
            [*self.stages, *_flatten(other)],
            strict=self.strict,
            resolve_mro=self.resolve_mro,
        )

    def __rrshift__(self, other: PipelineStage) -> Pipeline:
        """Chain this pipeline after ``other``, flattening nested stages."""
        if not isinstance(other, (Agent, Pipeline)):
            return NotImplemented
        return Pipeline(
            [*_flatten(other), *self.stages],
            strict=self.strict,
            resolve_mro=self.resolve_mro,
        )

    def run(self, value: Any, *, verbose: bool = False) -> Any:
        """Execute all stages synchronously.

        If a stage returns an awaitable, raises ``AdaptronError`` directing
        the caller to ``arun()`` (post-v1 async support).
        """
        for stage in self.stages:
            stage_input = value
            try:
                value = stage(value)
            except Exception as exc:
                if _is_adapter_stage(stage):
                    raise PipelineExecutionError(
                        stage.name,
                        stage_input,
                        source_type=stage.input_type,
                        target_type=stage.output_type,
                    ) from exc
                raise PipelineExecutionError(stage.name, stage_input) from exc
            if inspect.isawaitable(value):
                if inspect.iscoroutine(value):
                    value.close()
                raise AdaptronError(
                    f"Pipeline stage {stage.name!r} returned an awaitable; "
                    "sync run() cannot await it. Use await pipeline.arun(...) "
                    "instead, or wrap a synchronous callable."
                )
            if verbose:
                log_stage(
                    stage.name,
                    stage.input_type,
                    stage.output_type,
                    stage_input,
                    value,
                )
        return value

    async def arun(self, value: Any, *, verbose: bool = False) -> Any:
        """Execute all stages, awaiting any awaitable stage outputs.

        Sync callables still work; async def agents / awaitable returns are
        awaited. Adapter and agent failures raise ``PipelineExecutionError``
        the same way as ``run()``.
        """
        for stage in self.stages:
            stage_input = value
            try:
                value = stage(value)
                if inspect.isawaitable(value):
                    value = await value
            except Exception as exc:
                if _is_adapter_stage(stage):
                    raise PipelineExecutionError(
                        stage.name,
                        stage_input,
                        source_type=stage.input_type,
                        target_type=stage.output_type,
                    ) from exc
                raise PipelineExecutionError(stage.name, stage_input) from exc
            if verbose:
                log_stage(
                    stage.name,
                    stage.input_type,
                    stage.output_type,
                    stage_input,
                    value,
                )
        return value
