# runtime Test Package

> 📅 Last Updated: 2026/08/12

## Purpose
`tests/runtime/` covers CelestialFlow's runtime infrastructure, including task envelopes, queues, hashing, counters, exception types, formatting utilities, and remaining-time estimation. It serves as the low-level foundation for the scheduling layer and Stage layer.

## Included Test Files
- `test_envelope.py`: `TaskEnvelope` attributes and hashing behavior.
- `test_errors.py`: Custom exception hierarchy.
- `test_format.py`: String truncation representation and table rendering utilities.
- `test_hash.py`: `make_hashable` and `object_to_hash`.
- `test_metrics.py`: Counters and runtime metrics aggregation.
- `test_queue.py`: Task input and output queues.
- `test_types.py`: Various runtime value objects, enums, and context wrappers.

## How to Run

```bash
pytest tests/runtime -v
pytest tests/runtime -k "hash or envelope or format" -v
```
