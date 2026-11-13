# src/celestialflow/ticker/core_handler.py

> 📅 Last Updated: 2026/11/13

`core_handler.py` defines `TickHandler`, the base class of all tick handlers, together with the module-level validation function `validate_tick_period()`. It specifies three things:

1. **How many ticks apart** a handler is triggered (`tick_period`);
2. Whether the current tick **hits** (`should_tick()`);
3. **What to do** when a callback raises (`handle_exception()`).

## TickHandler

```python
class TickHandler:
    tick_period: int = 1

    def should_tick(self, event: TickEvent) -> bool: ...
    def set_tick_period(self, tick_period: int) -> None: ...
    def on_tick(self, event: TickEvent) -> None: ...
    def handle_exception(self, exception: Exception) -> None: ...
```

| Member | Description |
|------|------|
| `tick_period` | Class attribute, default `1` (triggered every tick). Subclasses may override it, or change it at runtime via `set_tick_period()` |
| `should_tick(event)` | Filter formula: `(event.seq - 1) % self.tick_period == 0` |
| `set_tick_period(tick_period)` | Sets a new tick count; raises `ConfigurationError` if less than `1` |
| `on_tick(event)` | Tick callback, no-op by default; subclasses only need to override it |
| `handle_exception(exception)` | Callback exception handling; by default `traceback.print_exception()` to standard error |

### Filter Formula

```text
hit condition: (seq - 1) % tick_period == 0
```

| `tick_period` | Hit `seq` | Actual Period (`Ticker.interval = 1.0`) |
|:-------------:|:------------:|:----------------------------------:|
| 1 | 1, 2, 3, 4, 5, 6, … | 1 second |
| 2 | 1, 3, 5, 7, 9, … | 2 seconds |
| 3 | 1, 4, 7, 10, … | 3 seconds |
| 5 | 1, 6, 11, 16, … | 5 seconds |

> Tick 1 always hits, so a handler does not need to wait an extra full period before starting work; the phase anchor is fixed at `seq == 1`.

### Runtime Speed Adjustment

`TickHub` and `Ticker` re-read the handler's current `tick_period` **before dispatching each tick**, so:

```python
handler.set_tick_period(5)   # takes effect from the next tick, no Ticker restart needed
```

Since filtering is still based on `seq`, the phase is re-anchored to `seq == 1` after the change. For example, changing from `tick_period=3` to `5` makes subsequent hits `1, 6, 11, …` instead of continuing to accumulate from the current index.

> You may also assign to `tick_period` directly, but that **does not trigger validation**; if you assign `0`, `should_tick()` raises `ZeroDivisionError` from the modulo. Always prefer `set_tick_period()`.

### Exception Handling Contract

| Scenario | Behavior |
|------|------|
| `on_tick()` raises (dispatched by `TickHub`) | `TickHub` catches it and calls that handler's `handle_exception()` |
| `on_tick()` raises (the handler is the root handler of `Ticker`) | `Ticker` catches it and calls that handler's `handle_exception()` |
| `handle_exception()` itself raises (the handler is inside a hub) | The exception propagates up to the hub's `handle_exception()` as the fallback |
| `handle_exception()` itself raises (the handler is the ticker root handler) | The exception escapes and terminates the background tick thread |
| Default implementation | `traceback.print_exception(exception)`, dispatch is not terminated |

To collect exceptions instead of printing them, just override `handle_exception()`:

```python
class CollectingHandler(TickHandler):
    def __init__(self) -> None:
        self.errors: list[Exception] = []

    def handle_exception(self, exception: Exception) -> None:
        self.errors.append(exception)
```

## validate_tick_period

```python
def validate_tick_period(handler: TickHandler) -> None: ...
```

Validates `handler.tick_period >= 1`, otherwise raises:

```text
ConfigurationError: tick_period must be a positive integer, got <value>
```

Callers:

- `TickHub.add_handler()`: validates when registering a sub-handler;
- `Ticker.__init__()`: validates the root handler at construction.

> This function is not re-exported by `celestialflow.ticker.__init__`; to reuse it in custom assembly code, use `from celestialflow.ticker.core_handler import validate_tick_period`.

## Usage Example

The example below does not start a background thread and directly validates `should_tick()` and runtime speed adjustment:

```python
from celestialflow.ticker import TickEvent, TickHandler


class RecordingHandler(TickHandler):
    tick_period = 3

    def __init__(self) -> None:
        self.hits: list[int] = []

    def on_tick(self, event: TickEvent) -> None:
        self.hits.append(event.seq)


def make_event(seq: int) -> TickEvent:
    return TickEvent(
        seq=seq,
        interval=1.0,
        scheduled_at=float(seq - 1),
        fired_at=float(seq - 1),
        wall_time=0.0,
        drift=0.0,
        skipped=0,
    )


handler = RecordingHandler()
for seq in range(1, 8):
    event = make_event(seq)
    if handler.should_tick(event):
        handler.on_tick(event)

print(handler.hits)  # [1, 4, 7]

handler.set_tick_period(2)
print([seq for seq in range(1, 7) if handler.should_tick(make_event(seq))])
# [1, 3, 5]
```

## Notes

1. **Handlers do not need to count themselves**: `TickHub` / `Ticker` have already performed the `should_tick()` filter before calling `on_tick()`.
2. **`tick_period` is a tick count, not seconds**: actual seconds = `Ticker.interval × tick_period`.
3. **Speed changes take effect immediately**: the dispatch path re-reads the attribute every tick, with no ticker restart needed.
4. **Exceptions are not swallowed silently**: they are only printed by default; if you need to report or count them, override `handle_exception()`, and make sure that callback never raises again, otherwise the tick thread may be terminated.
5. **Base class callbacks are all no-ops**: after inheriting `TickHandler`, you only need to override `on_tick()`.
