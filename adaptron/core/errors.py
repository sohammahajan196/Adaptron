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
