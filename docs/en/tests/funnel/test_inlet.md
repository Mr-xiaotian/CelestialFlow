# Inlet Basic Tests (test_inlet.py)

> 📅 Last Updated: 2026/08/19

## Purpose
Verifies the minimal responsibility of `celestialflow.funnel.core_inlet.BaseInlet`: accepting data from the caller via `_funnel()`, placing it into the target queue, and having it consumed by a running `BaseSpout` subclass.

## Coverage Points
- `MockInlet.send()` forwards records via `_funnel()`.
- `MockSpout` consumes both string and dictionary messages from the queue.
- When the consumer is not started, records should still enter the queue first and be available for subsequent reads.

## Test Coverage Matrix

| Test Class | Case | Coverage Target |
|--------|------|----------|
| `TestBaseInlet` | `test_inlet_to_spout_communication` | After starting the spout, the two messages injected by the inlet are eventually consumed in order |
| `TestBaseInlet` | `test_funnel_puts_record_into_queue` | When the spout is not started, `_funnel()` directly puts the raw record into the target queue |
| `TestBaseInlet` | `test_bind_spout_creates_bound_inlet` | `bind_spout()` returns an inlet sharing state with the target spout |

## How to Run

```bash
pytest tests/funnel/test_inlet.py -v
pytest tests/funnel/test_inlet.py -k "communication" -v
```
