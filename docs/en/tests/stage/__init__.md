# stage Test Package

> 📅 Last Updated: 2026/08/26

## Purpose
`tests/stage/` covers `TaskStage`, `TaskExecutor`, and the execution semantics of built-in Stage components, verifying task input, output, deduplication, termination signals, concurrency modes, and lifecycle behavior.

## Included Test Files
- `test_executor.py`: `TaskExecutor` execution modes, retry, deduplication, `restore_db` recovery, and configuration validation.
- `test_stage.py`: `TaskStage` basic lifecycle and configuration validation.
- `test_stages.py`: Built-in Stage components such as splitter and router.
- `test_dispatch.py`: Core behavior tests for `TaskDispatch` across three scheduling modes (serial/thread/async).

## How to Run

```bash
pytest tests/stage -v
pytest tests/stage -k "executor or stage" -v
```
