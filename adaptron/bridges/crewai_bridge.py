"""CrewAI bridge — duck-typed ``can_wrap``/``adapt`` for CrewAI agents/crews.

Probed by ``wrap()`` **after** the LangChain bridge and **before** the
plain-Python fallback (PLAN.md §2.4, Milestone 6): a CrewAI ``Agent`` or
``Crew`` is also a plain callable under the hood (or would otherwise be
mis-classified), so the generic path would lose its kickoff calling
convention.

Importing this module never requires ``crewai`` to be installed —
``can_wrap`` is pure duck-typing against the *object* passed in, not the
``crewai`` package. Only ``adapt`` lazily imports ``crewai``, solely to
fail loudly with an actionable ``WrapError`` if the extra isn't installed
(bridges.mdc). Core (`adaptron/core/`) never imports this module or
``crewai``.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from adaptron.core.agent import Agent
from adaptron.core.errors import WrapError

# CrewAI Agent (1.x): role/goal identity plus standalone ``kickoff`` —
# narrower than a bare callable, and distinct from LangChain's
# invoke/batch/stream surface.
_AGENT_ATTRS = ("role", "goal")
# CrewAI Crew: agent/task lists plus ``kickoff(inputs=...)``.
_CREW_ATTRS = ("agents", "tasks")


def can_wrap(obj: Any) -> bool:
    """Return ``True`` if ``obj`` duck-types as a CrewAI agent or crew.

    Checks narrower, more specific signatures than a bare callable
    (PLAN.md §2.4): either a CrewAI ``Agent`` (``role`` + ``goal`` plus
    callable ``.kickoff``) or a ``Crew`` (``agents`` + ``tasks`` plus
    callable ``.kickoff``). Never imports ``crewai`` or checks
    ``isinstance`` against its types — structural only.
    """
    return _is_agent(obj) or _is_crew(obj)


def _is_agent(obj: Any) -> bool:
    return callable(getattr(obj, "kickoff", None)) and all(
        hasattr(obj, attr) for attr in _AGENT_ATTRS
    )


def _is_crew(obj: Any) -> bool:
    return callable(getattr(obj, "kickoff", None)) and all(
        hasattr(obj, attr) for attr in _CREW_ATTRS
    )


def _unwrap_output(result: Any) -> Any:
    """Prefer ``.raw`` from CrewAI output objects; otherwise pass through."""
    if inspect.isawaitable(result):
        raise WrapError(
            "Cannot wrap CrewAI object: kickoff returned an awaitable, but "
            "Adaptron v1 only supports synchronous run(). Use a sync CrewAI "
            "Agent/Crew kickoff outside an async event loop, or await the "
            "result yourself before handing values into an Adaptron pipeline."
        )
    # LiteAgentOutput / CrewOutput expose `.raw`; prefer it so default
    # str→str ports see a plain value rather than the framework wrapper.
    if hasattr(result, "raw"):
        return result.raw
    return result


def _call_agent(obj: Any, value: Any) -> Any:
    return _unwrap_output(obj.kickoff(value))


def _call_crew(obj: Any, value: Any) -> Any:
    # Crew.kickoff expects ``inputs: dict | None``. Non-dicts are wrapped
    # under ``"input"`` so the bridge's default ``str → str`` ports remain
    # usable for simple demos; pass a dict when task templates need named
    # placeholders.
    inputs = value if isinstance(value, dict) else {"input": value}
    return _unwrap_output(obj.kickoff(inputs=inputs))


def _resolve_caller(obj: Any) -> Callable[[Any, Any], Any]:
    """Return the call helper for a duck-typed CrewAI agent or crew."""
    if _is_agent(obj):
        return _call_agent
    if _is_crew(obj):
        return _call_crew
    raise WrapError(
        f"Cannot wrap {type(obj).__name__!r} as a CrewAI agent/crew: expected "
        "an Agent (role, goal, kickoff) or a Crew (agents, tasks, kickoff). "
        "Pass a CrewAI Agent/Crew, or use wrap() with a plain callable instead."
    )


def adapt(
    obj: Any,
    *,
    input_type: Any = str,
    output_type: Any = str,
    name: str = "",
) -> Agent:
    """Wrap a duck-typed CrewAI agent or crew into an ``Agent``.

    Delegates calls to ``obj.kickoff`` — positional messages for Agents,
    ``inputs=`` for Crews. Ports default to ``str -> str`` unless overridden;
    CrewAI return shapes vary, so framework output objects are unwrapped to
    ``.raw`` when present (PLAN.md §3 Milestone 6).

    Args:
        obj: The CrewAI object to wrap; should satisfy ``can_wrap``.
        input_type: Explicit input type; defaults to ``str``.
        output_type: Explicit output type; defaults to ``str``.
        name: Explicit name; defaults to ``obj``'s class name.

    Returns:
        An ``Agent`` whose ``__call__`` delegates to ``obj.kickoff``.

    Raises:
        WrapError: If the ``crewai`` package is not installed, ``obj`` is
            not a supported Agent/Crew shape, or ``kickoff`` returns an
            awaitable (async is out of scope for v1).
    """
    try:
        import crewai  # type: ignore[import-not-found]  # noqa: F401
    except ImportError as exc:
        raise WrapError(
            "Cannot wrap as a CrewAI agent: the 'crewai' package is not "
            "installed. Install it with: pip install adaptron[crewai]"
        ) from exc

    call_fn = _resolve_caller(obj)

    def _call(value: Any) -> Any:
        return call_fn(obj, value)

    return Agent(
        _call,
        input_type=input_type,
        output_type=output_type,
        name=name or type(obj).__name__,
    )
