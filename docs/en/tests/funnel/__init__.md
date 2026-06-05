# funnel Test Package

> Last Updated: 2026/06/05

## Purpose
`tests/funnel/` covers thread lifecycle and queue transport semantics for the basic funnel components, mainly validating the minimum behavioral contract of `BaseInlet` and `BaseSpout`.

## Included Test Files
- `test_inlet.py`: Verifies that the inlet writes records into the target queue through `_funnel()`.
- `test_spout.py`: Verifies spout lifecycle hooks, termination handling, and the abstract-method contract.

## How to Run

```bash
pytest tests/funnel -v
pytest tests/funnel -k "inlet or spout" -v
```

