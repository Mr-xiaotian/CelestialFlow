# TaskProgress

> 📅 Last updated: 2026/04/22

The TaskProgress module provides task progress visualization based on `tqdm`.

## Features

- **Dynamic Updates**: Supports dynamically increasing the total task count (`add_total`), adapting to streaming tasks or task splitting scenarios.
- **Multi-mode Support**: 
  - Normal mode: Uses standard `tqdm`.
  - Async mode: Uses `tqdm.asyncio`, suitable for `async` execution mode.
- **Null Mode**: `NullTaskProgress` is a null implementation for when the progress bar display is disabled, avoiding `if show_progress` checks throughout the code.

## Usage

Initialize in a `TaskExecutor` or `TaskStage`:

```python
self.task_progress = TaskProgress(
    total_tasks=0,  # Initially usually 0; increases dynamically as tasks arrive
    desc="Processing",
    mode="normal"
)
```

Update progress:

```python
self.task_progress.update(1)
```

Dynamically increase the total:

```python
self.task_progress.add_total(100)
```
