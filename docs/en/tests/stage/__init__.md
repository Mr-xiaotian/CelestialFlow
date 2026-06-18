# stage Test Package

> 📅 Last Updated: 2026/06/18

## Purpose
`tests/stage/` covers `TaskStage`, `TaskExecutor`, and the execution semantics of built-in Stage components, verifying task input, output, deduplication, termination signals, concurrency modes, and lifecycle behavior.

## Included Test Files
- `test_executor.py`: `TaskExecutor` execution and queue consumption.
- `test_stage.py`: `TaskStage` basic lifecycle and configuration validation.
- `test_stages.py`: Built-in Stage components such as splitter and router.

## How to Run

```bash
pytest tests/stage -v
pytest tests/stage -k "executor or stage" -v
```
