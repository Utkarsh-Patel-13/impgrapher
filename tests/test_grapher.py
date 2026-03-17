"""Tests for impgraph.grapher."""

from __future__ import annotations

from pathlib import Path

import pytest

from impgraph.grapher import Grapher
from impgraph.models import ImportRecord, ModuleNode


def _make_result(*pairs: tuple[str, list[str]]) -> dict:
    """Build a minimal WalkResult from (module_name, [imported_names]) pairs."""
    result = {}
    for mod, imports in pairs:
        records = [
            ImportRecord(
                module_name=imp,
                is_stdlib=False,
                is_relative=False,
                source_file=Path(f"{mod}.py"),
            )
            for imp in imports
        ]
        result[mod] = ModuleNode(name=mod, path=Path(f"{mod}.py"), imports=records)
    return result


def test_builds_digraph_from_walk_result():
    wr = _make_result(("a", ["requests"]), ("b", ["flask"]))
    g = Grapher(wr)
    assert "a" in g._graph.nodes
    assert "b" in g._graph.nodes


def test_node_kinds_local_vs_external():
    wr = _make_result(("mymod", ["requests"]))
    g = Grapher(wr)
    assert g._graph.nodes["mymod"]["kind"] == "local"
    assert g._graph.nodes["requests"]["kind"] == "external"


def test_get_cycles_detects_cycle():
    wr = _make_result(("a", ["b"]), ("b", ["a"]))
    g = Grapher(wr)
    cycles = g.get_cycles()
    assert len(cycles) > 0


def test_get_cycles_empty_for_dag():
    wr = _make_result(("a", ["b"]), ("b", ["c"]))
    g = Grapher(wr)
    assert g.get_cycles() == []


def test_get_metrics_returns_all_keys():
    wr = _make_result(("a", ["b"]))
    g = Grapher(wr)
    metrics = g.get_metrics()
    for node in g._graph.nodes:
        assert "in_degree" in metrics[node]
        assert "out_degree" in metrics[node]
        assert "pagerank" in metrics[node]


def test_render_matplotlib_creates_file(tmp_path):
    wr = _make_result(("mymod", ["requests"]))
    g = Grapher(wr, fmt="png")
    out = tmp_path / "graph.png"
    result = g.render(out)
    assert result.exists()
    assert result.stat().st_size > 0


def test_render_html_creates_file(tmp_path):
    pytest.importorskip("pyvis")
    wr = _make_result(("mymod", ["requests"]))
    g = Grapher(wr)
    out = tmp_path / "graph.html"
    result = g.render_html(out)
    assert result.exists()
    content = result.read_text()
    assert "<html" in content.lower()


def test_to_json_serializable_structure():
    wr = _make_result(("a", ["b"]))
    g = Grapher(wr)
    data = g.to_json_serializable()
    assert "nodes" in data
    assert "edges" in data
    assert any(n["id"] == "a" for n in data["nodes"])
