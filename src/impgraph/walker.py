"""AST-based Python import walker."""

from __future__ import annotations

import ast
import os
from pathlib import Path

from impgraph.models import ImportRecord, ModuleNode, WalkResult
from impgraph.stdlib_compat import is_stdlib

__all__ = ["Walker"]

EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        "venv",
        ".venv",
        "__pycache__",
        "node_modules",
        ".git",
        ".vscode",
        ".idea",
        "dist",
        "build",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".eggs",
        "*.egg-info",
    }
)


def _module_name_from_path(file_path: Path, root: Path) -> str:
    """Derive a dotted module name from a file path relative to root."""
    try:
        rel = file_path.relative_to(root)
    except ValueError:
        rel = file_path
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else file_path.stem


def _extract_imports(
    source: str,
    file_path: Path,
    *,
    include_stdlib: bool,
    include_relative: bool,
) -> list[ImportRecord]:
    """Parse *source* and return ImportRecord list."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    records: list[ImportRecord] = []
    seen: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name in seen:
                    continue
                seen.add(name)
                stdlib = is_stdlib(name)
                if not include_stdlib and stdlib:
                    continue
                records.append(
                    ImportRecord(
                        module_name=name,
                        is_stdlib=stdlib,
                        is_relative=False,
                        source_file=file_path,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            level = node.level or 0
            relative = level > 0
            if relative and not include_relative:
                continue
            module = node.module or ""
            if relative:
                name = "." * level + module
            else:
                name = module
            if not name or name in seen:
                continue
            seen.add(name)
            stdlib = (not relative) and is_stdlib(name)
            if not include_stdlib and stdlib:
                continue
            records.append(
                ImportRecord(
                    module_name=name,
                    is_stdlib=stdlib,
                    is_relative=relative,
                    source_file=file_path,
                )
            )

    return records


class Walker:
    """Walk a file or directory tree and extract Python import data."""

    def __init__(
        self,
        path: str | Path,
        *,
        include_stdlib: bool = False,
        include_relative: bool = True,
    ) -> None:
        self._root = Path(path).resolve()
        if not self._root.exists():
            raise FileNotFoundError(f"Path does not exist: {self._root}")
        self._include_stdlib = include_stdlib
        self._include_relative = include_relative

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def walk(self) -> WalkResult:
        """Return a mapping of module-name → ModuleNode for all .py files found."""
        result: WalkResult = {}
        if self._root.is_file():
            self._process_file(self._root, self._root.parent, result)
        else:
            self._walk_dir(self._root, result)
        return result

    def save_as_json(self, walk_result: WalkResult, output_path: str | Path) -> None:
        """Serialise *walk_result* to JSON at *output_path*."""
        import json

        output_path = Path(output_path)
        data = {
            name: {
                "path": str(node.path),
                "imports": [
                    {
                        "module_name": rec.module_name,
                        "is_stdlib": rec.is_stdlib,
                        "is_relative": rec.is_relative,
                    }
                    for rec in node.imports
                ],
            }
            for name, node in walk_result.items()
        }
        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _walk_dir(self, directory: Path, result: WalkResult) -> None:
        with os.scandir(directory) as it:
            for entry in it:
                name = entry.name
                # Skip excluded dirs
                if entry.is_dir(follow_symlinks=False):
                    if name in EXCLUDED_DIRS or name.endswith(".egg-info"):
                        continue
                    self._walk_dir(Path(entry.path), result)
                elif entry.is_file() and name.endswith(".py"):
                    self._process_file(Path(entry.path), self._root, result)

    def _process_file(self, file_path: Path, root: Path, result: WalkResult) -> None:
        source = file_path.read_text(encoding="utf-8", errors="replace")
        mod_name = _module_name_from_path(file_path, root)
        imports = _extract_imports(
            source,
            file_path,
            include_stdlib=self._include_stdlib,
            include_relative=self._include_relative,
        )
        node = ModuleNode(name=mod_name, path=file_path, imports=imports)
        result[mod_name] = node
