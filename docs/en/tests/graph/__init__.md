# graph Test Package

> Last Updated: 2026/06/05

## Purpose
`tests/graph/` covers task-graph construction, topology analysis, structure export, and graph-level scheduling behavior, mainly corresponding to the `celestialflow.graph` module.

## Included Test Files
- `test_analysis.py`: Covers source-node detection, level computation, and NetworkX-based graph analysis helpers.
- `test_graph.py`: Covers graph construction, scheduling, error collection, and lifecycle behavior of `TaskGraph`.
- `test_serialize.py`: Covers JSON / text export logic for structure graphs.

## How to Run

```bash
pytest tests/graph -v
pytest tests/graph -k "graph or analysis" -v
```

