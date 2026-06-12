# runtime Test Package

> 📅 Last Updated: 2026/06/05

## Purpose
`tests/runtime/` covers CelestialFlow's runtime infrastructure, including task envelopes, queues, hashing, counters, exception types, and remaining-time estimation. It serves as the low-level foundation for the scheduling layer and Stage layer.

## Included Test Files
- `test_dispatch.py`: Dispatch loop and distribution logic.
- `test_envelope.py`: `TaskEnvelope` attributes and hashing behavior.
- `test_errors.py`: Custom exception hierarchy.
- `test_estimators.py`: Elapsed-time and remaining-time estimation algorithms.
- `test_hash.py`: `make_hashable` and `object_to_hash`.
- `test_metrics.py`: Counters and runtime metrics aggregation.
- `test_queue.py`: Task input and output queues.
- `test_types.py`: Various runtime value objects, enums, and context wrappers.

## How to Run

```bash
pytest tests/runtime -v
pytest tests/runtime -k "hash or envelope or estimators" -v
```
