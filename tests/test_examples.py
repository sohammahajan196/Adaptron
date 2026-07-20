"""E2E tests for example pipelines — Milestone 8 (PLAN.md §3 / §4)."""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from adaptron.core import adapters as adapters_module

_EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def _load_example(module_stem: str) -> ModuleType:
    """Load ``examples/<stem>.py`` without requiring a package ``__init__``."""
    path = _EXAMPLES_DIR / f"{module_stem}.py"
    name = f"adaptron_examples_{module_stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load example module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _isolated_registry() -> Any:
    """Snapshot/restore the global adapter registry so examples don't leak."""
    original = dict(adapters_module._registry)
    yield
    adapters_module._registry.clear()
    adapters_module._registry.update(original)


def test_plain_python_example_output_and_default_adapter() -> None:
    """Bare ``adaptron`` quickstart example — no framework extras required."""
    example = _load_example("plain_python_pipeline")
    pipeline = example.build_pipeline()

    assert any(s.name == "adapter<str->dict>" for s in pipeline.stages)
    assert pipeline.run("hello adaptron") == {"words": 2}


def test_plain_python_example_verbose_logs_adapter(
    caplog: pytest.LogCaptureFixture,
) -> None:
    example = _load_example("plain_python_pipeline")
    pipeline = example.build_pipeline()

    with caplog.at_level(logging.INFO, logger="adaptron"):
        result = pipeline.run("hello adaptron", verbose=True)

    assert result == {"words": 2}
    messages = [rec.getMessage() for rec in caplog.records if rec.name == "adaptron"]
    assert any("adapter<str->dict>" in msg for msg in messages)
    assert any("to_upper" in msg for msg in messages)
    assert any("word_count" in msg for msg in messages)


def test_cross_framework_example_mock_with_adapter(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Mock mode: gated on extras, no API keys; asserts auto-adaptation."""
    pytest.importorskip("langchain")
    pytest.importorskip("crewai")

    example = _load_example("cross_framework_pipeline")
    pipeline = example.build_pipeline(live=False)

    adapter_names = [s.name for s in pipeline.stages if s.name.startswith("adapter<")]
    assert "adapter<Message->str>" in adapter_names
    assert [s.name for s in pipeline.stages] == [
        "langchain_researcher",
        "adapter<Message->str>",
        "crewai_writer",
        "format_result",
    ]

    with caplog.at_level(logging.INFO, logger="adaptron"):
        result = pipeline.run("adaptron", verbose=True)

    assert result["status"] == "ok"
    assert "LC mock research" in result["draft"]
    assert "CrewAI mock draft" in result["draft"]

    messages = [rec.getMessage() for rec in caplog.records if rec.name == "adaptron"]
    assert any("adapter<Message->str>" in msg for msg in messages)
    assert any("langchain_researcher" in msg for msg in messages)
    assert any("crewai_writer" in msg for msg in messages)
    assert any("format_result" in msg for msg in messages)
