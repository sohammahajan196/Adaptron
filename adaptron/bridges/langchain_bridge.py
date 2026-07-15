"""LangChain bridge — duck-typed ``can_wrap``/``adapt`` for LangChain agents.

Probed by ``wrap()`` **before** the plain-Python fallback (PLAN.md §2.4,
Milestone 5): a LangChain ``Runnable``/``Chain`` is also a plain callable
under the hood, so the generic path would otherwise swallow it and lose
its invoke/run calling convention.

Importing this module never requires ``langchain`` to be installed —
``can_wrap`` is pure duck-typing against the *object* passed in, not the
``langchain`` package. Only ``adapt`` lazily imports ``langchain``, solely
to fail loudly with an actionable ``WrapError`` if the extra isn't
installed (bridges.mdc). Core (`adaptron/core/`) never imports this module
or ``langchain``.
"""

from __future__ import annotations

import typing
from collections.abc import Callable
from typing import Any

from adaptron.core.agent import Agent
from adaptron.core.errors import WrapError

# Runnable interface (LangChain 0.1+/1.x): invoke/batch/stream all present
# together is a much stronger signal than a bare `.invoke` alone, which
# could coincidentally match unrelated plain-Python objects.
_RUNNABLE_ATTRS = ("invoke", "batch", "stream")
# Legacy `Chain` interface: callable `.run` plus the input/output key
# declarations every `Chain` subclass carries.
_LEGACY_CHAIN_ATTRS = ("input_keys", "output_keys")

_PREFERRED_CALL_METHODS = ("invoke", "run")


def can_wrap(obj: Any) -> bool:
    """Return ``True`` if ``obj`` duck-types as a LangChain agent/chain.

    Checks narrower, more specific signatures than a bare callable
    (PLAN.md §2.4): either the modern ``Runnable`` interface (callable
    ``.invoke``, ``.batch``, and ``.stream`` all present), or the legacy
    ``Chain`` interface (callable ``.run`` plus ``.input_keys``/
    ``.output_keys``). Never imports ``langchain`` or checks ``isinstance``
    against its types — structural only.
    """
    is_runnable = all(callable(getattr(obj, attr, None)) for attr in _RUNNABLE_ATTRS)
    is_legacy_chain = callable(getattr(obj, "run", None)) and all(
        hasattr(obj, attr) for attr in _LEGACY_CHAIN_ATTRS
    )
    return is_runnable or is_legacy_chain


def _resolve_call_method(obj: Any) -> Callable[[Any], Any]:
    """Return ``obj``'s preferred call method: ``.invoke`` over ``.run``."""
    for name in _PREFERRED_CALL_METHODS:
        method = getattr(obj, name, None)
        if callable(method):
            return typing.cast(Callable[[Any], Any], method)
    raise WrapError(
        f"Cannot wrap {type(obj).__name__!r} as a LangChain agent: no callable "
        "'invoke' or 'run' method found. Pass a LangChain Runnable/Chain/"
        "AgentExecutor, or use wrap() with a plain callable instead."
    )


def adapt(
    obj: Any,
    *,
    input_type: Any = str,
    output_type: Any = str,
    name: str = "",
) -> Agent:
    """Wrap a duck-typed LangChain agent/chain into an ``Agent``.

    Delegates calls to ``obj.invoke`` (preferred) or ``obj.run`` (legacy
    ``Chain``\\ s). Ports default to ``str -> str`` unless overridden —
    LangChain's own return shapes vary by construct, so no attempt is made
    to normalize them here (PLAN.md §3 Milestone 5).

    Args:
        obj: The LangChain object to wrap; should satisfy ``can_wrap``.
        input_type: Explicit input type; defaults to ``str``.
        output_type: Explicit output type; defaults to ``str``.
        name: Explicit name; defaults to ``obj``'s class name.

    Returns:
        An ``Agent`` whose ``__call__`` delegates to ``obj``'s invoke/run
        method.

    Raises:
        WrapError: If the ``langchain`` package is not installed, or
            ``obj`` exposes neither a callable ``invoke`` nor ``run``
            method.
    """
    try:
        import langchain  # type: ignore[import-not-found]  # noqa: F401
    except ImportError as exc:
        raise WrapError(
            "Cannot wrap as a LangChain agent: the 'langchain' package is not "
            "installed. Install it with: pip install adaptron[langchain]"
        ) from exc

    call_method = _resolve_call_method(obj)

    def _call(value: Any) -> Any:
        return call_method(value)

    return Agent(
        _call,
        input_type=input_type,
        output_type=output_type,
        name=name or type(obj).__name__,
    )
