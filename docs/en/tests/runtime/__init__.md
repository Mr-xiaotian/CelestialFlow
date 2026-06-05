# runtime Test Package

> Last Updated: 2026/06/05

## Purpose
`tests/runtime/` covers CelestialFlow runtime infrastructure, including task envelopes, queues, hashes, counters, exception types, and remaining-time estimation. It is the low-level safety net for the dispatch layer and stage layer.

## Included Test Files
- `test_dispatch.py`: Dispatch loop and routing logic.
- `test_envelope.py`: `TaskEnvelope` properties and hash behavior.
- `test_errors.py`: Custom exception hierarchy.
- `test_estimators.py`: Elapsed-time and remaining-time estimation algorithms.
- `test_hash.py`: `make_hashable` and `object_to_hash`.
- `test_metrics.py`: Counters and runtime metric aggregation.
- `test_queue.py`: Task input/output queues.
- `test_types.py`: Runtime value objects, enums, and context wrappers.

## How to Run

```bash
pytest tests/runtime -v
pytest tests/runtime -k "hash or envelope or estimators" -v
```

