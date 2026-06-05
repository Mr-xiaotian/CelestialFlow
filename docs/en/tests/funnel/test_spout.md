# Base Spout Tests (test_spout.py)

> Last Updated: 2026/06/05

## Purpose
Validates the lifecycle hooks, termination handling, and abstract-method contract of `celestialflow.funnel.core_spout.BaseSpout`, ensuring the listener thread starts, stops, and drains records before shutdown as expected.

## Coverage
- `start()` calls `_before_start()`.
- `stop()` triggers `_after_stop()` and stops consuming newly queued records after shutdown.
- The base class raises `CelestialFlowError` when `_handle_record()` is not implemented.

## Key Scenarios
- `test_base_spout_lifecycle`: Verifies lifecycle hooks and that data queued before shutdown is still consumed.
- `test_spout_termination_signal`: Verifies that repeated `stop()` calls are safe and that records enqueued after termination are no longer processed.
- `test_spout_not_implemented_error`: Verifies the error message when the abstract handler is not overridden.

## How to Run

```bash
pytest tests/funnel/test_spout.py -v
pytest tests/funnel/test_spout.py -k "lifecycle or termination" -v
```

