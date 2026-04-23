# util_queue

> 📅 Last updated: 2026/04/22

`runtime/util_queue.py` provides cleanup utility functions for multiprocessing queues.

## cleanup_mpqueue

```python
def cleanup_mpqueue(queue: MPQueue) -> None:
    """
    Drains and closes a multiprocessing queue (multiprocessing.Queue),
    used to release resources and avoid BrokenPipeError on process exit.
    """
```

Typically called during process termination or abnormal exit to ensure that residual data in the multiprocessing queue is discarded and the queue is properly closed and joined.
