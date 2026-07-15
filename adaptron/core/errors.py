"""Adaptron exception hierarchy (grows with milestones — PLAN.md §3)."""

from __future__ import annotations


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
