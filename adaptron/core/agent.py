"""Agent — wraps a callable with a name and single input/output type (PLAN.md §2.1)."""

from __future__ import annotations

import inspect
import typing
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from adaptron.core.errors import WrapError

if TYPE_CHECKING:
    from adaptron.core.pipeline import Pipeline, PipelineStage


def _target_for_introspection(obj: Any) -> Callable[..., Any]:
    """Return the function-like object to introspect for signature/type hints.

    Plain functions and methods carry their own ``__globals__`` and
    annotations directly. Callable *instances* (classes implementing
    ``__call__``) need their bound ``__call__`` method instead, so ``self``
    is excluded from the signature and hints resolve against the class's
    defining module.
    """
    if inspect.isroutine(obj):
        return typing.cast(Callable[..., Any], obj)
    return typing.cast(Callable[..., Any], obj.__call__)


def _resolve_io_types(obj: Any) -> tuple[Any, Any]:
    """Infer ``(input_type, output_type)`` from type hints, defaulting to ``Any``.

    Used only when the caller hasn't supplied an explicit override — see
    ``Agent``'s priority order.
    """
    target = _target_for_introspection(obj)

    try:
        hints = typing.get_type_hints(target)
    except Exception:
        hints = {}

    try:
        signature = inspect.signature(target)
    except (TypeError, ValueError):
        signature = None

    input_type: Any = Any
    if signature is not None:
        positional = [
            p
            for p in signature.parameters.values()
            if p.kind
            not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        ]
        if positional:
            input_type = hints.get(positional[0].name, Any)

    output_type = hints.get("return", Any)
    return input_type, output_type


@dataclass
class Agent:
    """Wraps a callable with a name and a single input/output type.

    Types are resolved in priority order (PLAN.md §2.1):

    1. Explicit ``input_type``/``output_type`` passed to the constructor.
    2. Inferred from ``typing`` hints on the wrapped callable
       (via ``inspect.signature`` + ``typing.get_type_hints``).
    3. ``typing.Any`` if neither is available.

    Attributes:
        func: The wrapped callable (a function or a callable instance).
        input_type: The single type this agent accepts.
        output_type: The single type this agent produces.
        name: A human-readable identifier, used in logs and error messages.
            Defaults to the callable's ``__name__`` (or its class name for
            callable instances).

    Calling an ``Agent`` delegates directly to the wrapped callable, passing
    through exactly one value in and one value out::

        agent = Agent(str.upper)
        agent("hi")  # "HI"
    """

    func: Callable[[Any], Any]
    input_type: Any = None
    output_type: Any = None
    name: str = ""

    def __post_init__(self) -> None:
        if not callable(self.func):
            raise WrapError(
                f"Cannot create Agent: expected a callable, got "
                f"{type(self.func).__name__!r}. Pass a function or a class "
                "instance implementing __call__, or use wrap() for framework "
                "agents."
            )

        if self.input_type is None or self.output_type is None:
            inferred_input, inferred_output = _resolve_io_types(self.func)
            if self.input_type is None:
                self.input_type = inferred_input
            if self.output_type is None:
                self.output_type = inferred_output

        if not self.name:
            self.name = getattr(self.func, "__name__", type(self.func).__name__)

    def __call__(self, value: Any) -> Any:
        """Invoke the wrapped callable with a single input value."""
        return self.func(value)

    def __rshift__(self, other: PipelineStage) -> Pipeline:
        """Chain ``other`` after this agent, building a ``Pipeline``.

        ``a >> b`` returns a ``Pipeline`` containing ``[a, b]``; if ``other``
        is itself a ``Pipeline``, its stages are flattened in rather than
        nested (PLAN.md §2.2).
        """
        from adaptron.core.pipeline import Pipeline, _flatten

        if not isinstance(other, (Agent, Pipeline)):
            return NotImplemented
        return Pipeline([self, *_flatten(other)])

    def __rrshift__(self, other: PipelineStage) -> Pipeline:
        """Chain this agent after ``other``, building a ``Pipeline``.

        Mirrors ``__rshift__`` so ``a >> b`` works regardless of which side
        defines the operator (PLAN.md §2.2).
        """
        from adaptron.core.pipeline import Pipeline, _flatten

        if not isinstance(other, (Agent, Pipeline)):
            return NotImplemented
        return Pipeline([*_flatten(other), self])
