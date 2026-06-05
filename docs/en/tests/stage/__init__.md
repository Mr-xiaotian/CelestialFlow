# stage Test Package

> Last Updated: 2026/06/05

## Purpose
`tests/stage/` covers the execution semantics of `TaskStage`, `TaskExecutor`, and built-in stage components, validating task input, output, deduplication, termination signals, concurrency modes, and lifecycle behavior.

## Included Test Files
- `test_executor.py`: `TaskExecutor` execution and queue consumption.
- `test_stage.py`: Basic `TaskStage` lifecycle.
- `test_stages.py`: Built-in stage components such as splitter, router, and transport.

## How to Run

```bash
pytest tests/stage -v
pytest tests/stage -k "executor or stage" -v
```

