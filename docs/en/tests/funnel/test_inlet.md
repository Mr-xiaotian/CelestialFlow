# Base Inlet Tests (test_inlet.py)

> Last Updated: 2026/06/05

## Purpose
Validates the minimum responsibility of `celestialflow.funnel.core_inlet.BaseInlet`: data passed in by the caller is forwarded into the target queue through `_funnel()` and consumed by a running `BaseSpout` subclass.

## Coverage
- `MockInlet.send()` forwards records through `_funnel()`.
- `MockSpout` consumes both string and dictionary messages from the queue.
- When no consumer is started yet, records should still enter the queue first for later retrieval.

## Key Scenarios
- `test_inlet_to_spout_communication`: Starts `MockSpout`, sends two messages, and verifies that the consumer receives them in order.
- `test_funnel_puts_record_into_queue`: Does not start the spout and directly asserts that the original record can be retrieved from the queue, confirming that `_funnel()` does not rewrite data.

## How to Run

```bash
pytest tests/funnel/test_inlet.py -v
pytest tests/funnel/test_inlet.py -k "communication" -v
```

