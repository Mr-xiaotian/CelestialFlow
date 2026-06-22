# Spout Basic Tests (test_spout.py)

> 📅 Last Updated: 2026/06/22

## Purpose
Verifies the lifecycle hooks, termination signal handling, and abstract method constraints of `celestialflow.funnel.core_spout.BaseSpout`, ensuring the listener thread can start, stop, and consume records before stopping as expected.

## Coverage Points
- `start()` calls `_before_start()`.
- `stop()` triggers `_after_stop()` and does not continue consuming new records after stopping.
- The base class raises `CelestialFlowError` when `_handle_record()` is not implemented.

## Key Scenarios
- `test_base_spout_lifecycle`: Verifies start/stop hooks and that "data before stopping is still consumed."
- `test_spout_termination_signal`: Verifies that repeated `stop()` calls are safe and that no further enqueued data is processed after termination.
- `test_spout_can_restart_after_stop`: Verifies that after `stop()`, calling `start()` again can recreate the background thread and continue consumption.
- `test_spout_not_implemented_error`: Verifies the error message when an abstract method is not overridden.

## How to Run

```bash
pytest tests/funnel/test_spout.py -v
pytest tests/funnel/test_spout.py -k "lifecycle or termination" -v
```
