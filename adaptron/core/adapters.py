"""Adapter registry — exact ``(source_type, target_type)`` lookup (PLAN.md §2.3).

Default adapters (``str → dict``, ``str → Message``) register automatically
when this module is imported — including via ``import adaptron`` — so demos
and construction-time resolution work with no extra user setup.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

AdapterFn = Callable[[Any], Any]

_registry: dict[tuple[type, type], AdapterFn] = {}


@dataclass(frozen=True)
class Message:
    """Demo message type used by the default ``str → Message`` adapter.

    Intended for docs and examples — not part of the public API exported
    from ``adaptron`` (import from ``adaptron.core.adapters`` when needed).
    """

    text: str


def register_adapter(source_type: type, target_type: type, fn: AdapterFn) -> None:
    """Register a converter for the exact ``(source_type, target_type)`` pair.

    Lookup is by exact type match only — no MRO walk, no ``isinstance``
    fallback (PLAN.md §2.3 v1 scope note: an adapter registered for a base
    class will *not* match a subclass instance). This keeps resolution
    O(1) via a plain dict lookup.

    Registering the same pair again overwrites the previous adapter and
    emits a ``UserWarning`` — never a silent overwrite.

    Args:
        source_type: The exact upstream output type this adapter accepts.
        target_type: The exact downstream input type this adapter produces.
        fn: A callable that converts a ``source_type`` value into a
            ``target_type`` value.
    """
    key = (source_type, target_type)
    if key in _registry:
        warnings.warn(
            f"register_adapter: overwriting existing adapter for "
            f"{source_type.__name__} -> {target_type.__name__}.",
            stacklevel=2,
        )
    _registry[key] = fn


def get_adapter(source_type: type, target_type: type) -> AdapterFn | None:
    """Look up the exact adapter registered for ``(source_type, target_type)``.

    O(1) dict lookup, used by ``Pipeline`` construction-time resolution
    (Phase 3 Task 3.3). Returns ``None`` when no exact-pair adapter is
    registered; callers decide whether that is acceptable (e.g. ``Any``
    on either side) or should raise ``NoAdapterError``.
    """
    return _registry.get((source_type, target_type))


def _str_to_dict(value: str) -> dict[str, str]:
    """Default ``str → dict`` adapter: wrap text as ``{\"text\": ...}``."""
    return {"text": value}


def _str_to_message(value: str) -> Message:
    """Default ``str → Message`` adapter for docs/demo pipelines."""
    return Message(text=value)


def _register_defaults() -> None:
    """Install the small default adapter set (PLAN.md §3 Milestone 3)."""
    register_adapter(str, dict, _str_to_dict)
    register_adapter(str, Message, _str_to_message)


_register_defaults()
