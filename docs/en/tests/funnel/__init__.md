# funnel Test Package

> 📅 Last Updated: 2026/06/05

## Purpose
`tests/funnel/` covers the thread lifecycle and queue transmission semantics of basic funnel components, primarily verifying the minimal behavioral constraints of `BaseInlet` and `BaseSpout`.

## Included Test Files
- `test_inlet.py`: Verifies that the inlet writes records to the target queue via `_funnel()`.
- `test_spout.py`: Verifies spout start/stop hooks, termination signal handling, and abstract method constraints.

## How to Run

```bash
pytest tests/funnel -v
pytest tests/funnel -k "inlet or spout" -v
```
