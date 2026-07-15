"""Adaptron — interconnect agents across frameworks via typed adapters.

Public API only (STRUCTURE.md): ``wrap``, ``register_adapter``, ``Pipeline``,
``Agent``. ``wrap()`` currently detects plain-Python callables only; the
LangChain and CrewAI bridges are probed ahead of this catch-all starting in
later milestones (PLAN.md §2.4) and are not wired in yet.
"""

from __future__ import annotations

import inspect
from typing import Any

from adaptron.core.agent import Agent
from adaptron.core.errors import WrapError

__all__ = ["Agent", "wrap"]


def wrap(
    obj: Any,
    *,
    input_type: Any = None,
    output_type: Any = None,
    name: str = "",
) -> Agent:
    """Wrap a plain-Python callable into an ``Agent``.

    Supports functions and callable instances (class instances implementing
    ``__call__``). Framework bridges are not probed yet — every object is
    handled by the plain-Python path in this milestone.

    Args:
        obj: The callable to wrap.
        input_type: Explicit input type override; skips inference for this
            port (PLAN.md §2.1).
        output_type: Explicit output type override; skips inference for
            this port.
        name: Explicit name override; defaults to the callable's
            ``__name__`` (or its class name for callable instances).

    Returns:
        An ``Agent`` wrapping ``obj``.

    Raises:
        WrapError: If ``obj`` is not callable, or is a class rather than an
            instance of one.
    """
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
