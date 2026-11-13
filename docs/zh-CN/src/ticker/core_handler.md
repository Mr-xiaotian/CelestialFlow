# src/celestialflow/ticker/core_handler.py

> 📅 最后更新日期: 2026/11/13

`core_handler.py` 定义所有节拍处理器的基类 `TickHandler`，以及模块级校验函数 `validate_tick_period()`。它规定了三件事：

1. 一个处理器**每隔多少拍**被触发（`tick_period`）；
2. 当前这一拍**是否命中**（`should_tick()`）；
3. 回调抛异常时**如何处理**（`handle_exception()`）。

## TickHandler

```python
class TickHandler:
    tick_period: int = 1

    def should_tick(self, event: TickEvent) -> bool: ...
    def set_tick_period(self, tick_period: int) -> None: ...
    def on_tick(self, event: TickEvent) -> None: ...
    def handle_exception(self, exception: Exception) -> None: ...
```

| 成员 | 说明 |
|------|------|
| `tick_period` | 类属性，默认 `1`（每拍触发）。子类可覆盖，也可在运行期通过 `set_tick_period()` 修改 |
| `should_tick(event)` | 过滤公式：`(event.seq - 1) % self.tick_period == 0` |
| `set_tick_period(tick_period)` | 设置新的拍数；小于 `1` 抛 `ConfigurationError` |
| `on_tick(event)` | 节拍回调，默认空实现；子类只需覆写它 |
| `handle_exception(exception)` | 回调异常处理，默认 `traceback.print_exception()` 打印到标准错误 |

### 过滤公式

```text
命中条件：(seq - 1) % tick_period == 0
```

| `tick_period` | 命中的 `seq` | 实际周期（`Ticker.interval = 1.0`） |
|:-------------:|:------------:|:----------------------------------:|
| 1 | 1, 2, 3, 4, 5, 6, … | 1 秒 |
| 2 | 1, 3, 5, 7, 9, … | 2 秒 |
| 3 | 1, 4, 7, 10, … | 3 秒 |
| 5 | 1, 6, 11, 16, … | 5 秒 |

> 第 1 拍始终命中，因此处理器不需要额外等待一个完整周期才开始工作；相位锚点固定为 `seq == 1`。

### 运行期调速

`TickHub` 与 `Ticker` 在**每一拍分发前**都会重新读取处理器当前的 `tick_period`，所以：

```python
handler.set_tick_period(5)   # 下一拍起生效，无需重启 Ticker
```

由于过滤仍以 `seq` 为基准，修改后相位会重新锚定到 `seq == 1`。例如从 `tick_period=3` 改为 `5`，后续命中变为 `1, 6, 11, …`，而不是从当前序号继续累加。

> 也可以直接给 `tick_period` 赋值，但这样**不会触发校验**；若赋值为 `0`，`should_tick()` 会因取模除零抛 `ZeroDivisionError`。建议始终使用 `set_tick_period()`。

### 异常处理契约

| 场景 | 行为 |
|------|------|
| `on_tick()` 抛异常（由 `TickHub` 分发） | `TickHub` 捕获后调用该处理器的 `handle_exception()` |
| `on_tick()` 抛异常（处理器是 `Ticker` 的根处理器） | `Ticker` 捕获后调用该处理器的 `handle_exception()` |
| `handle_exception()` 自身再抛（处理器在 hub 内） | 异常向上传播给 hub 的 `handle_exception()` 兜底 |
| `handle_exception()` 自身再抛（处理器是 ticker 根处理器） | 异常逃逸并终止后台节拍线程 |
| 默认实现 | `traceback.print_exception(exception)`，不终止分发 |

需要收集而不是打印异常时，覆写 `handle_exception()` 即可：

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

校验 `handler.tick_period >= 1`，否则抛：

```text
ConfigurationError: tick_period must be a positive integer, got <value>
```

调用方：

- `TickHub.add_handler()`：注册子处理器时校验；
- `Ticker.__init__()`：构造时校验根处理器。

> 该函数没有被 `celestialflow.ticker.__init__` 再导出；如需在自定义装配代码中复用，请 `from celestialflow.ticker.core_handler import validate_tick_period`。

## 使用示例

下面的示例不启动后台线程，直接验证 `should_tick()` 与运行期调速：

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

## 注意事项

1. **处理器无需自行计数**：`TickHub` / `Ticker` 在调用 `on_tick()` 前已经完成 `should_tick()` 过滤。
2. **`tick_period` 是拍数而非秒数**：实际秒数 = `Ticker.interval × tick_period`。
3. **调速立即生效**：分发路径每拍重新读取属性，不需要重启节拍器。
4. **异常不吞没**：默认只打印；若需要上报或统计，请覆写 `handle_exception()`，并注意不要让该回调自身再抛异常，否则可能终止节拍线程。
5. **基类回调都是空实现**：继承 `TickHandler` 后只需覆写 `on_tick()`。
