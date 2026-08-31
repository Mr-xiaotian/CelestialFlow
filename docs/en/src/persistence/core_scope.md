# funnel_scope

> 📅 Last Updated: 2026/08/26

`persistence/core_scope.py` provides the context manager `funnel_scope` for managing the global funnel lifecycle, used to uniformly start and stop `LifecycleSpout` and `LogSpout`.

## Core Object

### funnel_scope

```python
@contextmanager
def funnel_scope() -> Generator[None, None, None]:
```

A single-layer context manager responsible for:

1. Starting the global `LifecycleSpout` and `LogSpout` in sequence when entering the scope.
2. Stopping `LogSpout` and `LifecycleSpout` in order when exiting the scope.
3. Collecting all exceptions that occur during entry and exit, and raising them as a single `ExceptionGroup`.

```python
from celestialflow.persistence import funnel_scope

with funnel_scope():
    # LifecycleSpout and LogSpout are now started
    # Execute business logic...
    ...
# When exiting the scope, both Spouts have been stopped
```

## Notes

1. **Single-layer scope**: the current implementation does not promise reuse semantics for nested scopes; each `funnel_scope` should be used independently.
2. **Exception handling**: exceptions raised during entry or exit are collected into a list and ultimately raised as an `ExceptionGroup`, so no exception information is lost.
3. **Stop order**: `LogSpout` is stopped first, then `LifecycleSpout`, to ensure logs are as complete as possible.
