"""Shared data models for impgraph."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["ImportRecord", "ModuleNode", "WalkResult"]


@dataclass
class ImportRecord:
    """Represents a single import found in a Python source file."""

    module_name: str
    is_stdlib: bool
    is_relative: bool
    source_file: Path


@dataclass
class ModuleNode:
    """Represents a Python module and all imports it makes."""

    name: str
    path: Path
    imports: list[ImportRecord] = field(default_factory=list)


# Map from module dotted-name → ModuleNode
WalkResult = dict[str, ModuleNode]
