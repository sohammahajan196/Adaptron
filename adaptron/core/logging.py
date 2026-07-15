"""Execution logging — stdlib ``adaptron`` logger (PLAN.md §3 Milestone 4).

Helpers here format one-line stage records for verbose ``Pipeline.run``.
Wiring into ``run(verbose=...)`` lands in Task 4.2; this module stays
stdlib-only and side-effect-light so truncation and formatting can be
unit-tested in isolation.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("adaptron")

_PREVIEW_MAX = 120


def preview(value: Any, *, max_len: int = _PREVIEW_MAX) -> str:
    """Return a truncated ``repr`` suitable for log lines.

    Never dumps unbounded payloads (PRD §6.5 / performance rules).
    """
    text = repr(value)
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _type_name(tp: Any) -> str:
    """Return a short display name for a type used in log lines."""
    if tp is Any:
        return "Any"
    name = getattr(tp, "__name__", None)
    if isinstance(name, str):
        return name
    return repr(tp)


def format_stage_record(
    name: str,
    input_type: Any,
    output_type: Any,
    stage_input: Any,
    stage_output: Any,
    *,
    max_len: int = _PREVIEW_MAX,
) -> str:
    """Build a one-line stage record (name, types, truncated previews).

    Format matches PRD §6.5: agent/adapter name, input/output types, and
    truncated input/output previews in a single diagnosable line.
    """
    in_name = _type_name(input_type)
    out_name = _type_name(output_type)
    in_preview = preview(stage_input, max_len=max_len)
    out_preview = preview(stage_output, max_len=max_len)
    return (
        f"stage={name!r} in={in_name} out={out_name} "
        f"input={in_preview} output={out_preview}"
    )


def log_stage(
    name: str,
    input_type: Any,
    output_type: Any,
    stage_input: Any,
    stage_output: Any,
    *,
    max_len: int = _PREVIEW_MAX,
) -> None:
    """Emit one INFO log line for a completed pipeline stage."""
    logger.info(
        format_stage_record(
            name,
            input_type,
            output_type,
            stage_input,
            stage_output,
            max_len=max_len,
        )
    )
