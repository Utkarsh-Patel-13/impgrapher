"""Tests for impgraph.walker."""

from __future__ import annotations

from pathlib import Path

import pytest

from impgraph.walker import Walker


def test_parses_import_statement(make_project):
    root = make_project({"mod.py": "import requests\n"})
    result = Walker(root).walk()
    assert "mod" in result
    names = [r.module_name for r in result["mod"].imports]
    assert "requests" in names


def test_parses_from_import(make_project):
    root = make_project({"mod.py": "from pathlib import Path\n"})
    result = Walker(root, include_stdlib=True).walk()
    names = [r.module_name for r in result["mod"].imports]
    assert "pathlib" in names


def test_excludes_stdlib_by_default(make_project):
    root = make_project({"mod.py": "import os\nimport requests\n"})
    result = Walker(root).walk()
    names = [r.module_name for r in result["mod"].imports]
    assert "os" not in names
    assert "requests" in names


def test_includes_stdlib_when_flagged(make_project):
    root = make_project({"mod.py": "import os\n"})
    result = Walker(root, include_stdlib=True).walk()
    names = [r.module_name for r in result["mod"].imports]
    assert "os" in names


def test_handles_syntax_error_gracefully(make_project):
    root = make_project({"bad.py": "def foo(\n"})
    result = Walker(root).walk()
    assert "bad" in result
    assert result["bad"].imports == []


def test_relative_import_flagged(make_project):
    root = make_project({"pkg/__init__.py": "", "pkg/mod.py": "from . import foo\n"})
    result = Walker(root).walk()
    mod = result.get("pkg.mod") or result.get("pkg/mod")
    assert mod is not None
    rel_imports = [r for r in mod.imports if r.is_relative]
    assert len(rel_imports) >= 1


def test_nonexistent_path_raises():
    with pytest.raises(FileNotFoundError):
        Walker("/nonexistent/path/does/not/exist")


def test_finds_all_py_files(make_project):
    root = make_project(
        {"a.py": "import requests\n", "b.py": "import flask\n", "c.py": "import django\n"}
    )
    result = Walker(root).walk()
    assert len(result) == 3


def test_excludes_venv_dir(make_project):
    root = make_project(
        {"main.py": "import requests\n", ".venv/lib/site.py": "import os\n"}
    )
    result = Walker(root).walk()
    # only main.py should be processed
    assert all(".venv" not in k for k in result.keys())


def test_no_double_counting(make_project):
    root = make_project({"mod.py": "import requests\nimport requests\n"})
    result = Walker(root).walk()
    names = [r.module_name for r in result["mod"].imports]
    assert names.count("requests") == 1


def test_nested_subdirectory(make_project):
    root = make_project(
        {
            "pkg/__init__.py": "",
            "pkg/sub/__init__.py": "",
            "pkg/sub/deep.py": "import requests\n",
        }
    )
    result = Walker(root).walk()
    deep_key = next((k for k in result if "deep" in k), None)
    assert deep_key is not None


def test_single_file_walk(make_project, tmp_path):
    f = tmp_path / "single.py"
    f.write_text("import requests\n", encoding="utf-8")
    result = Walker(f).walk()
    assert len(result) == 1
    names = [r.module_name for r in list(result.values())[0].imports]
    assert "requests" in names
