# Spout Basic Tests (test_spout.py)

> 📅 Last Updated: 2026/08/19

## Purpose
Verifies the lifecycle hooks, termination signal handling, and abstract method constraints of `celestialflow.funnel.core_spout.BaseSpout`, ensuring the listener thread can start, stop, and consume records before stopping as expected.

## Coverage Points
- `start()` calls `_before_start()`.
- `stop()` triggers `_after_stop()` and does not continue consuming new records after stopping.
- The base class raises `CelestialFlowError` when `_handle_record()` is not implemented.

## Test Coverage Matrix

| Test Class | Case | Coverage Target |
|--------|------|----------|
| `TestBaseSpout` | `test_base_spout_lifecycle` | Start/stop hooks fire correctly, and data before stopping is still consumed |
| `TestBaseSpout` | `test_spout_termination_signal` | Repeated `stop()` calls are safe, and no further enqueued data is processed after termination |
| `TestBaseSpout` | `test_spout_can_restart_after_stop` | After `stop()`, calling `start()` again recreates the background thread and continues consumption |
| `TestBaseSpout` | `test_spout_not_implemented_error` | Raises `CelestialFlowError` when abstract method `_handle_record` is not overridden |

## How to Run

```bash
pytest tests/funnel/test_spout.py -v
pytest tests/funnel/test_spout.py -k "lifecycle or termination" -v
```
