"""Typer + Rich CLI for impgraph."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from impgraph.grapher import Grapher
from impgraph.walker import Walker

__all__ = ["app"]

app = typer.Typer(name="impgraph", add_completion=False, help="Visualise Python import graphs.")
console = Console()
err_console = Console(stderr=True, style="bold red")


@app.command("graph")
def graph_cmd(
    path: str = typer.Argument(..., help="File or directory to analyse"),
    output: str = typer.Option("graph.png", "-o", "--output", help="Output file path"),
    layout: str = typer.Option("dot", "-l", "--layout", help="Graphviz layout engine"),
    fmt: str = typer.Option("png", "-f", "--format", help="Output format (png, svg, pdf, …)"),
    json_out: Optional[str] = typer.Option(None, "-j", "--json", help="Also write JSON to this path"),
    stdlib: bool = typer.Option(False, "--stdlib", help="Include stdlib imports"),
    no_relative: bool = typer.Option(False, "--no-relative", help="Exclude relative imports"),
    pygraphviz: bool = typer.Option(False, "--pygraphviz", help="Use pygraphviz backend"),
    cycles: bool = typer.Option(False, "--cycles", help="Print detected import cycles"),
    metrics: bool = typer.Option(False, "--metrics", help="Print per-module metrics table"),
    html: bool = typer.Option(False, "--html", "-H", help="Also write interactive HTML graph"),
) -> None:
    """Render the import dependency graph for PATH."""
    target = Path(path)
    if not target.exists():
        err_console.print(f"Path not found: {target}")
        raise typer.Exit(code=1)

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        progress.add_task("Walking imports…", total=None)
        try:
            walker = Walker(target, include_stdlib=stdlib, include_relative=not no_relative)
            result = walker.walk()
        except Exception as exc:  # noqa: BLE001
            err_console.print(f"Error during walk: {exc}")
            raise typer.Exit(code=1) from exc

    if not result:
        err_console.print("No Python files found.")
        raise typer.Exit(code=1)

    grapher = Grapher(result, layout=layout, fmt=fmt)

    if json_out:
        walker.save_as_json(result, json_out)
        console.print(f"[green]JSON written to {json_out}[/green]")

    try:
        out = grapher.render(output, use_pygraphviz=pygraphviz)
        console.print(f"[green]Graph written to {out}[/green]")
    except Exception as exc:  # noqa: BLE001
        err_console.print(f"Render failed: {exc}")
        raise typer.Exit(code=1) from exc

    if html:
        html_path = Path(output).with_suffix(".html")
        grapher.render_html(html_path)
        console.print(f"[green]HTML graph written to {html_path}[/green]")

    if cycles:
        found = grapher.get_cycles()
        if found:
            console.print(f"[yellow]Cycles detected ({len(found)}):[/yellow]")
            for cyc in found:
                console.print("  " + " → ".join(cyc + [cyc[0]]))
        else:
            console.print("[green]No cycles detected.[/green]")

    if metrics:
        data = grapher.get_metrics()
        tbl = Table(title="Module Metrics", show_header=True)
        tbl.add_column("Module")
        tbl.add_column("In-degree", justify="right")
        tbl.add_column("Out-degree", justify="right")
        tbl.add_column("PageRank", justify="right")
        for mod, vals in sorted(data.items(), key=lambda x: -x[1]["pagerank"]):
            tbl.add_row(
                mod,
                str(vals["in_degree"]),
                str(vals["out_degree"]),
                f"{vals['pagerank']:.4f}",
            )
        console.print(tbl)


@app.command("info")
def info_cmd(
    path: str = typer.Argument(..., help="File or directory to analyse"),
    stdlib: bool = typer.Option(False, "--stdlib", help="Include stdlib imports"),
) -> None:
    """Print a table of modules and their imports (no rendering required)."""
    target = Path(path)
    if not target.exists():
        err_console.print(f"Path not found: {target}")
        raise typer.Exit(code=1)

    try:
        walker = Walker(target, include_stdlib=stdlib)
        result = walker.walk()
    except Exception as exc:  # noqa: BLE001
        err_console.print(f"Error: {exc}")
        raise typer.Exit(code=1) from exc

    if not result:
        console.print("[yellow]No Python files found.[/yellow]")
        return

    tbl = Table(title=f"Imports in {path}", show_header=True, show_lines=True)
    tbl.add_column("Module", style="bold cyan")
    tbl.add_column("Imports")
    for mod_name, node in sorted(result.items()):
        imports_str = ", ".join(r.module_name for r in node.imports) or "[dim]none[/dim]"
        tbl.add_row(mod_name, imports_str)
    console.print(tbl)
