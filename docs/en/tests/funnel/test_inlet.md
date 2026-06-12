# Inlet Basic Tests (test_inlet.py)

> 📅 Last Updated: 2026/06/05

## Purpose
Verifies the minimal responsibility of `celestialflow.funnel.core_inlet.BaseInlet`: accepting data from the caller via `_funnel()`, placing it into the target queue, and having it consumed by a running `BaseSpout` subclass.

## Coverage Points
- `MockInlet.send()` forwards records via `_funnel()`.
- `MockSpout` consumes both string and dictionary messages from the queue.
- When the consumer is not started, records should still enter the queue and be available for subsequent reads.

## Key Scenarios
- `test_inlet_to_spout_communication`: Starts `MockSpout`, sends two messages, and verifies the consumer receives them in order.
- `test_funnel_puts_record_into_queue`: Without starting the spout, directly asserts that the raw record is in the queue, confirming `_funnel()` does not mutate the data.

## How to Run

```bash
pytest tests/funnel/test_inlet.py -v
pytest tests/funnel/test_inlet.py -k "communication" -v
```
