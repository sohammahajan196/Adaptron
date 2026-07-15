"""Adaptron — interconnect agents across frameworks via typed adapters.

Public API only (STRUCTURE.md): ``wrap``, ``register_adapter``, ``Pipeline``,
``Agent``. ``wrap()`` probes bridges before the plain-Python catch-all, most
specific first (PLAN.md §2.4): LangChain → (CrewAI, Phase 6) → plain-Python.
A bridge is skipped entirely if its framework isn't installed, so core never
hard-depends on it. Registered adapters are not yet consulted during
``Pipeline`` construction — that wiring lands in Task 3.3.
"""

from __future__ import annotations

import inspect
from typing import Any

from adaptron.core.adapters import register_adapter
from adaptron.core.agent import Agent
from adaptron.core.errors import WrapError
from adaptron.core.pipeline import Pipeline

__all__ = ["Agent", "Pipeline", "register_adapter", "wrap"]


def _bridge_kwargs(input_type: Any, output_type: Any, name: str) -> dict[str, Any]:
    """Build ``adapt()`` overrides, omitting unset values.

    Bridges default their own ports (e.g. LangChain's ``str -> str``); only
    forward overrides the caller actually supplied so those defaults still
    apply when they didn't.
    """
    kwargs: dict[str, Any] = {}
    if input_type is not None:
        kwargs["input_type"] = input_type
    if output_type is not None:
        kwargs["output_type"] = output_type
    if name:
        kwargs["name"] = name
    return kwargs


def _try_langchain_bridge(
    obj: Any, *, input_type: Any, output_type: Any, name: str
) -> Agent | None:
    """Probe the LangChain bridge; ``None`` if unavailable or not a match.

    Skipped entirely (returns ``None``, no error) when ``langchain`` isn't
    installed — this is what keeps it optional (PLAN.md §2.4).
    """
    try:
        import langchain  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        return None

    from adaptron.bridges import langchain_bridge

    if not langchain_bridge.can_wrap(obj):
        return None
    return langchain_bridge.adapt(
        obj, **_bridge_kwargs(input_type, output_type, name)
    )


def wrap(
    obj: Any,
    *,
    input_type: Any = None,
    output_type: Any = None,
    name: str = "",
) -> Agent:
    """Wrap an agent — LangChain, (CrewAI, Phase 6), or plain Python — as an ``Agent``.

    Probe order (most specific first, PLAN.md §2.4): LangChain bridge, then
    the CrewAI bridge slot (Phase 6), then the plain-Python catch-all
    (functions and callable instances). Each bridge is skipped, not an
    error, when its framework isn't installed.

    Args:
        obj: The object to wrap.
        input_type: Explicit input type override; skips inference for this
            port (PLAN.md §2.1) and overrides a bridge's own default.
        output_type: Explicit output type override; skips inference for
            this port and overrides a bridge's own default.
        name: Explicit name override; defaults to the callable's
            ``__name__`` (or its class name for callable instances/bridged
            objects).

    Returns:
        An ``Agent`` wrapping ``obj``.

    Raises:
        WrapError: If ``obj`` matches a bridge but that bridge can't adapt
            it, or if ``obj`` is not callable, or is a class rather than an
            instance of one (plain-Python path).
    """
    langchain_agent = _try_langchain_bridge(
        obj, input_type=input_type, output_type=output_type, name=name
    )
    if langchain_agent is not None:
        return langchain_agent

    # CrewAI bridge slot (Phase 6): probed here, between LangChain and the
    # plain-Python fallback below (PLAN.md §2.4 probe order).

    if inspect.isclass(obj):
        raise WrapError(
            f"Cannot wrap {obj.__name__!r}: got a class, not an instance. "
            f"Pass an instance instead, e.g. wrap({obj.__name__}())."
        )
    if not callable(obj):
        raise WrapError(
            f"Cannot wrap {obj!r}: object of type {type(obj).__name__!r} is not "
            "callable. Pass a function or a class instance implementing __call__."
        )
    return Agent(obj, input_type=input_type, output_type=output_type, name=name)
