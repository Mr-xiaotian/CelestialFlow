# utils Test Package

> 📅 Last Updated: 2026/06/11

## Purpose
`tests/utils/` covers CelestialFlow general utility functions, including graph structure cloning and terminal-formatted output.

## Included Test Files
- `test_clone.py`: Validates deep-copy and independence of `clone_executor`, `clone_stage`, and `clone_graph`.
- `test_format.py`: Validates `format_repr` (string truncation and escaping) and `format_table` (terminal table rendering).

## How to Run

```bash
pytest tests/utils -v
pytest tests/utils -k "clone or format" -v
```
