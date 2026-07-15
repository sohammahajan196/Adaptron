"""Adaptron exception hierarchy (grows with milestones — PLAN.md §3)."""

from __future__ import annotations

from typing import Any

_INPUT_PREVIEW_MAX = 120


def _input_preview(value: Any, *, max_len: int = _INPUT_PREVIEW_MAX) -> str:
    """Return a truncated ``repr`` suitable for error messages."""
    text = repr(value)
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


class AdaptronError(Exception):
    """Base class for all Adaptron errors.

    Subclasses should carry enough context to diagnose failures without
    reading Adaptron source: stage/object involved, types when relevant,
    and a concrete fix when one exists.
    """


class WrapError(AdaptronError):
    """Raised when ``wrap()`` cannot turn an object into an ``Agent``.

    Message contract (actionable, PRD §6.1 / §7 Debuggability):

    - Name **what** failed to wrap (type and a short description).
    - Explain **why** it is unusable (e.g. not callable, missing interface).
    - Tell the caller **how** to fix it (pass a function, a ``__call__``
      instance, or — once bridges land — a supported framework agent).

    Example::

        raise WrapError(
            f"Cannot wrap {type(obj).__name__!r}: object is not callable. "
            "Pass a function, a class instance with __call__, or a supported "
            "framework agent."
        )
    """


class PipelineExecutionError(AdaptronError):
    """Raised when a stage fails during ``Pipeline.run()``.

    Raised (Milestone 2 / Phase 2) when any stage raises while the pipeline
    is executing: execution halts and this error carries which stage failed
    and the input that stage received (PRD §6.6, PLAN.md §3 Milestone 2).
    Prefer ``raise PipelineExecutionError(...) from cause`` so the original
    exception is preserved as ``__cause__``.

    Attributes:
        stage_name: Name of the stage that raised.
        stage_input: Value passed into that stage (full object; the message
            uses a truncated preview).

    Message contract (actionable, PRD §7 Debuggability):

    - Name **which** stage failed.
    - Show a **preview** of the input it received.
    - Tell the caller **how** to investigate (fix the stage or upstream).

    Example::

        raise PipelineExecutionError(
            stage.name,
            value,
        ) from exc
    """

    stage_name: str
    stage_input: Any

    def __init__(
        self,
        stage_name: str,
        stage_input: Any = None,
        *,
        message: str | None = None,
    ) -> None:
        self.stage_name = stage_name
        self.stage_input = stage_input
        if message is None:
            preview = _input_preview(stage_input)
            message = (
                f"Pipeline stage {stage_name!r} failed while processing "
                f"input {preview}. Inspect that stage's callable, or the "
                "upstream output that produced this input."
            )
        super().__init__(message)


def _type_name(tp: Any) -> str:
    """Return a short display name for a type used in error messages."""
    if tp is Any:
        return "Any"
    name = getattr(tp, "__name__", None)
    if isinstance(name, str):
        return name
    return repr(tp)


class NoAdapterError(AdaptronError):
    """Raised when adjacent pipeline stages have incompatible types.

    Raised at **construction** time (Milestone 3 / Phase 3) when chaining
    with ``>>`` if the left stage's output type does not match the right
    stage's input type and no exact ``(source, target)`` adapter is
    registered (PLAN.md §2.3, PRD §6.6). This is never deferred to
    ``run()``.

    Attributes:
        source_type: Output type of the upstream stage.
        target_type: Input type of the downstream stage.

    Message contract (actionable, PRD §7 Debuggability):

    - Name **both** mismatched types.
    - Suggest the exact ``register_adapter(...)`` call to fix it.

    Example::

        raise NoAdapterError(str, dict)
        # suggests: register_adapter(str, dict, fn)
    """

    source_type: Any
    target_type: Any

    def __init__(
        self,
        source_type: Any,
        target_type: Any,
        *,
        message: str | None = None,
    ) -> None:
        self.source_type = source_type
        self.target_type = target_type
        if message is None:
            src = _type_name(source_type)
            tgt = _type_name(target_type)
            message = (
                f"No adapter for {src} -> {tgt}. "
                f"Register one with: register_adapter({src}, {tgt}, fn)"
            )
        super().__init__(message)
