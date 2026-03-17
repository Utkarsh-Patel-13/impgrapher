"""NetworkX + Matplotlib rendering for impgraph (no system Graphviz required)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx

from impgraph.models import WalkResult

__all__ = ["Grapher"]

# Maps CLI layout names → NetworkX layout callables
_LAYOUT_MAP: dict[str, Any] = {
    "dot": None,          # handled by _hierarchical_layout (topological)
    "neato": None,        # kamada_kawai — stress-minimising, similar to neato
    "fdp": None,          # spring — force-directed
    "sfdp": None,         # spring
    "circo": None,        # circular
    "twopi": None,        # shell
    "spring": None,       # alias
    "circular": None,     # alias
    "spectral": None,     # spectral
    "kamada_kawai": None, # alias
}

VALID_LAYOUTS: frozenset[str] = frozenset(_LAYOUT_MAP)

# Node colours
_COLOR_LOCAL = "#4A90D9"
_COLOR_EXTERNAL = "#5BAD72"


def _hierarchical_layout(g: nx.DiGraph) -> dict[str, tuple[float, float]]:
    """Left-to-right hierarchical layout via topological generations (DAG-safe)."""
    try:
        generations = list(nx.topological_generations(g))
    except nx.NetworkXUnfeasible:
        return nx.spring_layout(g, seed=42)  # type: ignore[return-value]
    pos: dict[str, tuple[float, float]] = {}
    for x, gen in enumerate(generations):
        nodes = sorted(gen)
        total = len(nodes)
        for i, node in enumerate(nodes):
            y = (total - 1) / 2.0 - i  # centre the column vertically
            pos[node] = (float(x), y)
    return pos


def _get_positions(g: nx.DiGraph, layout: str) -> dict[str, tuple[float, float]]:
    if layout in ("dot", "neato") or layout not in VALID_LAYOUTS:
        # neato is stress-minimising — kamada_kawai is the closest pure-Python equivalent
        if layout == "neato":
            try:
                return nx.kamada_kawai_layout(g)  # type: ignore[return-value]
            except Exception:
                pass
        return _hierarchical_layout(g)
    if layout in ("fdp", "sfdp", "spring"):
        return nx.spring_layout(g, seed=42)  # type: ignore[return-value]
    if layout in ("circo", "circular"):
        return nx.circular_layout(g)  # type: ignore[return-value]
    if layout == "twopi":
        return nx.shell_layout(g)  # type: ignore[return-value]
    if layout in ("spectral",):
        return nx.spectral_layout(g)  # type: ignore[return-value]
    if layout == "kamada_kawai":
        return nx.kamada_kawai_layout(g)  # type: ignore[return-value]
    return _hierarchical_layout(g)


class Grapher:
    """Build and render a directed import graph from a WalkResult."""

    def __init__(
        self,
        walk_result: WalkResult,
        *,
        layout: str = "dot",
        fmt: str = "png",
    ) -> None:
        self._walk_result = walk_result
        self._layout = layout if layout in VALID_LAYOUTS else "dot"
        self._fmt = fmt
        self._graph: nx.DiGraph = self._build_graph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(
        self,
        output_path: str | Path,
        *,
        use_pygraphviz: bool = False,
    ) -> Path:
        """Render the import graph to *output_path* (pure-Python by default)."""
        output_path = Path(output_path)
        if use_pygraphviz:
            return self._render_pygraphviz(output_path)
        return self._render_matplotlib(output_path)

    def render_html(self, output_path: str | Path) -> Path:
        """Render an interactive HTML graph using pyvis."""
        try:
            from pyvis.network import Network  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError("pyvis is required for HTML output: pip install pyvis") from exc

        output_path = Path(output_path)
        net = Network(height="750px", width="100%", directed=True, notebook=False)

        for node, data in self._graph.nodes(data=True):
            color = _COLOR_LOCAL if data.get("kind") == "local" else _COLOR_EXTERNAL
            shape = "box" if data.get("kind") == "local" else "ellipse"
            net.add_node(node, label=node, color=color, shape=shape)

        for src, dst in self._graph.edges():
            net.add_edge(src, dst)

        net.write_html(str(output_path))
        return output_path

    def get_cycles(self) -> list[list[str]]:
        """Return all simple cycles in the import graph."""
        return list(nx.simple_cycles(self._graph))

    def get_metrics(self) -> dict[str, dict[str, Any]]:
        """Return per-module in-degree, out-degree, and PageRank."""
        if self._graph.number_of_edges() > 0:
            try:
                pr = nx.pagerank(self._graph)
            except Exception:
                n = self._graph.number_of_nodes()
                pr = {node: 1.0 / n for node in self._graph.nodes()} if n > 0 else {}
        else:
            pr = {}
        return {
            node: {
                "in_degree": self._graph.in_degree(node),
                "out_degree": self._graph.out_degree(node),
                "pagerank": pr.get(node, 0.0),
            }
            for node in self._graph.nodes()
        }

    def to_json_serializable(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation of the graph."""
        return {
            "nodes": [
                {"id": n, "kind": d.get("kind", "unknown")}
                for n, d in self._graph.nodes(data=True)
            ],
            "edges": [{"source": u, "target": v} for u, v in self._graph.edges()],
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_graph(self) -> nx.DiGraph:
        g: nx.DiGraph = nx.DiGraph()
        local_names = set(self._walk_result.keys())

        for mod_name, node in self._walk_result.items():
            g.add_node(mod_name, kind="local")
            for rec in node.imports:
                if rec.is_relative:
                    continue
                target = rec.module_name
                kind = "local" if target in local_names else "external"
                if target not in g:
                    g.add_node(target, kind=kind)
                g.add_edge(mod_name, target)

        return g

    def _render_matplotlib(self, output_path: Path) -> Path:
        import matplotlib  # type: ignore[import-untyped]
        matplotlib.use("Agg")  # non-interactive backend — no display needed
        import matplotlib.pyplot as plt  # type: ignore[import-untyped]

        g = self._graph
        pos = _get_positions(g, self._layout)

        local_nodes = [n for n, d in g.nodes(data=True) if d.get("kind") == "local"]
        ext_nodes = [n for n, d in g.nodes(data=True) if d.get("kind") != "local"]

        # Scale figure size with node count
        n = max(g.number_of_nodes(), 1)
        fig_size = max(10, n * 0.8)
        fig, ax = plt.subplots(figsize=(fig_size, fig_size * 0.6))
        ax.set_axis_off()

        pos_kw: dict[str, Any] = dict(pos=pos, ax=ax)

        nx.draw_networkx_nodes(g, nodelist=local_nodes, node_color=_COLOR_LOCAL,
                               node_shape="s", node_size=1800, **pos_kw)
        nx.draw_networkx_nodes(g, nodelist=ext_nodes, node_color=_COLOR_EXTERNAL,
                               node_shape="o", node_size=1400, **pos_kw)
        nx.draw_networkx_labels(g, font_size=8, font_color="white", **pos_kw)
        nx.draw_networkx_edges(
            g, edge_color="#888888", arrows=True,
            arrowstyle="-|>", arrowsize=15,
            connectionstyle="arc3,rad=0.05",
            pos=pos, ax=ax,
        )

        plt.tight_layout()
        fmt = output_path.suffix.lstrip(".") or self._fmt
        plt.savefig(output_path, format=fmt, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def _render_pygraphviz(self, output_path: Path) -> Path:
        try:
            import pygraphviz as pgv  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "pygraphviz is required for --pygraphviz: pip install impgraph[pygraphviz]"
            ) from exc

        ag = pgv.AGraph(directed=True, strict=False)
        ag.graph_attr["rankdir"] = "LR"

        for node, data in self._graph.nodes(data=True):
            if data.get("kind") == "local":
                ag.add_node(node, shape="box", style="filled",
                            fillcolor=_COLOR_LOCAL, fontcolor="white")
            else:
                ag.add_node(node, shape="ellipse", style="filled",
                            fillcolor=_COLOR_EXTERNAL, fontcolor="white")

        for src, dst in self._graph.edges():
            ag.add_edge(src, dst)

        ag.layout(prog=self._layout)
        ag.draw(str(output_path))
        return output_path
