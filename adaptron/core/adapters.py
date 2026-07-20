"""Adapter registry — exact ``(source_type, target_type)`` lookup (PLAN.md §2.3).

Default adapters (``str → dict``, ``str → Message``) register automatically
when this module is imported — including via ``import adaptron`` — so demos
and construction-time resolution work with no extra user setup.

Post-v1: optional MRO-aware lookup (and thereby many-subclass → one target
coercion) via ``get_adapter(..., mro=True)`` / ``Pipeline(resolve_mro=True)``.
Exact-pair remains the default.
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

    Lookup defaults to exact type match only. With ``Pipeline(resolve_mro=True)``
    or ``get_adapter(..., mro=True)``, a registered base-class pair can also
    serve subclasses (many-to-one coercion via MRO).

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


def _mro_types(tp: Any) -> tuple[type, ...]:
    """Return an MRO-like sequence for adapter resolution."""
    if tp is Any or not isinstance(tp, type):
        return ()
    return tp.__mro__


def get_adapter(
    source_type: type,
    target_type: type,
    *,
    mro: bool = False,
) -> AdapterFn | None:
    """Look up an adapter for ``(source_type, target_type)``.

    Exact ``(source, target)`` wins. When ``mro=True``, also search registered
    pairs along ``source_type``'s MRO × ``target_type``'s MRO, preferring the
    most specific source then most specific target (first hits in each MRO).
    If multiple equally specific pairs exist at different MRO depths, the
    earliest source-MRO match wins; ambiguous same-depth pairs raise
    ``AmbiguousAdapterError`` only when two different callables tie — for
    simplicity we take the first discovered in source-major order.

    Args:
        source_type: Upstream output type.
        target_type: Downstream input type.
        mro: Enable subclass / many-to-one base-adapter matching.

    Returns:
        The adapter callable, or ``None`` if unresolved.
    """
    exact = _registry.get((source_type, target_type))
    if exact is not None or not mro:
        return exact

    best: AdapterFn | None = None
    best_key: tuple[int, int] | None = None
    for i, src in enumerate(_mro_types(source_type)):
        for j, tgt in enumerate(_mro_types(target_type)):
            fn = _registry.get((src, tgt))
            if fn is None:
                continue
            key = (i, j)
            if best_key is None or key < best_key:
                best_key = key
                best = fn
    return best


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
