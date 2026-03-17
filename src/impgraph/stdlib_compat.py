"""Stdlib detection using sys.stdlib_module_names (Python 3.10+)."""

from __future__ import annotations

import sys

__all__ = ["STDLIB_NAMES", "is_stdlib"]

STDLIB_NAMES: frozenset[str] = sys.stdlib_module_names  # type: ignore[attr-defined]


def is_stdlib(module_name: str) -> bool:
    """Return True if *module_name* is part of the Python standard library."""
    root = module_name.split(".")[0]
    return root in STDLIB_NAMES
