[![PyPI version](https://badge.fury.io/py/impgraph.svg)](https://pypi.python.org/pypi/impgraph/) [![GitHub license](https://img.shields.io/github/license/Naereen/StrapDown.js.svg)](https://github.com/Utkarsh-Patel-13/impgrapher/blob/master/LICENSE)

# impgraph

Visualise the import dependency graph of any Python project or file.

- **AST-based** parsing — accurate, handles all import forms
- **Pure-Python rendering** via matplotlib — no system Graphviz required
- **Interactive HTML** output via pyvis — hover, drag, zoom
- **Cycle detection** and **per-module metrics** (in/out-degree, PageRank)
- **Rich** terminal output with progress spinner and tables

---

## Installation

```bash
pip install impgraph
```

No system dependencies required — rendering is done entirely in Python via matplotlib.

To use the `pygraphviz` backend (requires system Graphviz + `brew install graphviz`):

```bash
pip install "impgraph[pygraphviz]"
```

---

## Quick start

```bash
# Print a table of modules and imports (no rendering needed)
impgraph info path/to/project

# Render a PNG dependency graph
impgraph graph path/to/project -o graph.png

# Also write an interactive HTML graph
impgraph graph path/to/project -o graph.png --html

# Show import cycles and per-module metrics
impgraph graph path/to/project --cycles --metrics
```

---

## Commands

### `impgraph graph <path>`

Render the import dependency graph for a file or directory.

| Flag | Default | Description |
|------|---------|-------------|
| `-o / --output` | `graph.png` | Output file path |
| `-f / --format` | `png` | Output format: `png`, `svg`, `pdf`, … |
| `-l / --layout` | `dot` | Graphviz layout: `dot`, `neato`, `fdp`, `circo`, `twopi`, … |
| `-j / --json` | — | Also write import data as JSON |
| `--html / -H` | off | Also write an interactive HTML graph |
| `--stdlib` | off | Include standard library imports |
| `--no-relative` | off | Exclude relative imports |
| `--pygraphviz` | off | Use pygraphviz backend instead of pure-Python graphviz |
| `--cycles` | off | Print detected import cycles |
| `--metrics` | off | Print per-module in/out-degree and PageRank table |

### `impgraph info <path>`

Print a Rich table of every module and its imports. No Graphviz required — useful in CI.

| Flag | Default | Description |
|------|---------|-------------|
| `--stdlib` | off | Include standard library imports |

---

## Visual legend

| Colour | Meaning |
|--------|---------|
| Blue box | Local module (part of the analysed project) |
| Green ellipse | External package |

---

## Notes

- Directories automatically excluded: `.venv`, `venv`, `__pycache__`, `.git`, `dist`, `build`, `.mypy_cache`, `.ruff_cache`, `node_modules`, `.vscode`, `.idea`
- Standard library detection uses `sys.stdlib_module_names` — always accurate for the running interpreter
- A single file can be passed instead of a directory

---

## Development

```bash
uv sync --all-extras
uv run pytest --cov
uv run mypy src/
uv run ruff check src/ tests/
```
