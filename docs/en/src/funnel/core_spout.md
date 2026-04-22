# BaseSpout

> 📅 Last updated: 2026/04/22

`BaseSpout` is the base class for all outlet classes, providing common functionality for listening to a queue and processing records in a background thread.

## Initialization

```python
class BaseSpout:
    def __init__(self):
        self.queue = MPQueue()  # Multi-process-safe queue
        self._thread: Thread | None = None
```

## Core Methods

### start

Starts the background listening thread.

```python
def start(self):
    """Start the background listening thread."""
```

Flow:
1. Call the `_before_start()` hook
2. Create and start a daemon thread that executes the `_spout()` method

### stop

Stops the listening thread and cleans up resources.

```python
def stop(self):
    """Stop the listening thread and clean up resources."""
```

Flow:
1. Send `TERMINATION_SIGNAL` to the queue
2. Wait for the thread to finish
3. Clean up queue resources (`cleanup_mpqueue`)
4. Call the `_after_stop()` hook

### get_queue

```python
def get_queue(self) -> MPQueue:
    """Return the queue object for use by the Inlet side."""
```

## Overridable Methods

```python
def _before_start(self):
    """Initialization operations before starting."""

def _handle_record(self, record):
    """Process a single record (subclasses must override)."""
    raise NotImplementedError

def _after_stop(self):
    """Cleanup operations after stopping."""
```

## Internal Implementation

```python
def _spout(self):
    """Listening loop, runs in a background thread."""
    while True:
        try:
            record = self.queue.get(timeout=0.5)
            if isinstance(record, TerminationSignal):
                break
            self._handle_record(record)
        except Empty:
            continue
```

## Notes

1. **Multi-process Safety**: Uses `multiprocessing.Queue` to ensure safe cross-process communication
2. **Daemon Thread**: The listening thread is set as a daemon thread and automatically terminates when the main process exits
3. **Graceful Shutdown**: Notifies the thread to stop by sending a `TerminationSignal`
4. **Queue Cleanup**: Remaining records in the queue are cleaned up when stopping
