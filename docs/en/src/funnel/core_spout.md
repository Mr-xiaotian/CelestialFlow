# BaseSpout

> 📅 Last Updated: 2026/05/15

`BaseSpout` is the base class for all spout classes, providing common functionality for listening to a queue in a background thread and processing records.

## Initialization

```python
class BaseSpout:
    def __init__(self):
        self.queue = Queue()  # Queue
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
1. Calls the `_before_start()` hook
2. Creates and starts a daemon thread that executes the `_spout()` method

### stop

Stops the listening thread and cleans up resources.

```python
def stop(self):
    """Stop the listening thread and clean up resources."""
```

Flow:
1. Sends `TERMINATION_SIGNAL` to the queue
2. Waits for the thread to finish (`join`) and sets `_thread` to `None`
3. Calls the `_after_stop()` hook

### get_queue

```python
def get_queue(self) -> Queue:
    """Returns the queue object for use by the Inlet side."""
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
    """Listening loop, runs in the background thread."""
    while True:
        try:
            record = self.queue.get(timeout=0.5)
            if isinstance(record, TerminationSignal):
                break
            self._handle_record(record)
        except Empty:
            continue
        except Exception:
            continue
```

## Notes

1. **Thread Safety**: Uses `queue.Queue` to ensure thread-safe communication
2. **Daemon Thread**: The listening thread is set as a daemon thread, automatically terminating when the main process exits
3. **Graceful Stop**: Notifies the thread to stop by sending a `TerminationSignal`
4. **Queue Cleanup**: Remaining records in the queue are not cleaned up on stop
