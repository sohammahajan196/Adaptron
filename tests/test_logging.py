"""Tests for verbose stage logging — Milestone 4 (PLAN.md §3)."""

from __future__ import annotations

import logging

import pytest
from adaptron import wrap
from adaptron.core.logging import format_stage_record, preview


def _to_str(n: int) -> str:
    return str(n)


def _consume_dict(d: dict[str, str]) -> int:
    return len(d["text"])


def test_preview_truncates_long_values() -> None:
    assert preview("hi") == repr("hi")
    long = preview("x" * 200)
    assert long.endswith("...")
    assert len(long) == 120


def test_format_stage_record_includes_name_types_previews() -> None:
    line = format_stage_record(
        "adapter<str->dict>",
        str,
        dict,
        "hi",
        {"text": "hi"},
    )
    assert "adapter<str->dict>" in line
    assert "in=str" in line
    assert "out=dict" in line
    assert "input=" in line and "output=" in line


def test_verbose_run_logs_stages_in_order_including_adapter(
    caplog: pytest.LogCaptureFixture,
) -> None:
    pipeline = wrap(_to_str) >> wrap(_consume_dict, input_type=dict)

    with caplog.at_level(logging.INFO, logger="adaptron"):
        result = pipeline.run(42, verbose=True)

    assert result == len("42")

    messages = [rec.getMessage() for rec in caplog.records if rec.name == "adaptron"]
    assert len(messages) == 3
    assert "_to_str" in messages[0]
    assert "in=int" in messages[0] and "out=str" in messages[0]
    assert "adapter<str->dict>" in messages[1]
    assert "in=str" in messages[1] and "out=dict" in messages[1]
    assert "_consume_dict" in messages[2]
    assert "in=dict" in messages[2] and "out=int" in messages[2]


def test_silent_run_emits_no_adaptron_stage_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    pipeline = wrap(_to_str) >> wrap(_consume_dict, input_type=dict)

    with caplog.at_level(logging.INFO, logger="adaptron"):
        result = pipeline.run(42)

    assert result == len("42")
    adaptron_messages = [
        rec.getMessage() for rec in caplog.records if rec.name == "adaptron"
    ]
    assert adaptron_messages == []
