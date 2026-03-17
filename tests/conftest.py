"""Shared fixtures for impgraph tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def make_project(tmp_path: Path):
    """Return a helper that writes {relative_path: source} files into tmp_path."""

    def _factory(files: dict[str, str]) -> Path:
        for rel, source in files.items():
            target = tmp_path / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding="utf-8")
        return tmp_path

    return _factory
