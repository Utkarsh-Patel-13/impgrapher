"""Tests for impgraph.cli."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from impgraph.cli import app

runner = CliRunner()


def test_graph_basic_invocation(make_project):
    root = make_project({"mymod.py": "import requests\n"})
    out = root / "graph.png"
    result = runner.invoke(app, ["graph", str(root), "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()


def test_graph_json_flag(make_project, tmp_path):
    root = make_project({"mymod.py": "import requests\n"})
    json_out = tmp_path / "out.json"
    out = tmp_path / "graph.png"
    result = runner.invoke(app, ["graph", str(root), "-o", str(out), "-j", str(json_out)])
    assert result.exit_code == 0
    assert json_out.exists()


def test_graph_cycles_flag(make_project, tmp_path):
    root = make_project({"a.py": "import b\n", "b.py": "import a\n"})
    out = tmp_path / "graph.png"
    result = runner.invoke(app, ["graph", str(root), "-o", str(out), "--cycles"])
    assert result.exit_code == 0
    assert "cycle" in result.output.lower()


def test_graph_metrics_flag(make_project, tmp_path):
    root = make_project({"mymod.py": "import requests\n"})
    out = tmp_path / "graph.png"
    result = runner.invoke(app, ["graph", str(root), "-o", str(out), "--metrics"])
    assert result.exit_code == 0
    assert "Module Metrics" in result.output


def test_graph_html_flag(make_project, tmp_path):
    pytest.importorskip("pyvis")
    root = make_project({"mymod.py": "import requests\n"})
    out = tmp_path / "graph.png"
    result = runner.invoke(app, ["graph", str(root), "-o", str(out), "--html"])
    assert result.exit_code == 0
    assert out.with_suffix(".html").exists()


def test_graph_invalid_path_exits_nonzero():
    result = runner.invoke(app, ["graph", "/nonexistent/path/xyz"])
    assert result.exit_code != 0


def test_info_command_prints_table(make_project):
    root = make_project({"mymod.py": "import requests\n"})
    result = runner.invoke(app, ["info", str(root)])
    assert result.exit_code == 0
    assert "mymod" in result.output
