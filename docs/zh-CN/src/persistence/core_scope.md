# funnel_scope

> 📅 最后更新日期: 2026/08/12

`persistence/core_scope.py` 提供了管理全局 funnel 生命周期的上下文管理器 `funnel_scope`，用于统一启动和停止 `FallbackSpout` 与 `LogSpout`。

## 核心对象

### funnel_scope

```python
@contextmanager
def funnel_scope() -> Generator[None, None, None]:
```

一个单层上下文管理器，负责：

1. 进入作用域时启动全局 `FallbackSpout` 和 `LogSpout`
2. 退出作用域时按顺序停止 `LogSpout` 和 `FallbackSpout`
3. 收集进入和退出过程中发生的所有异常，统一以 `ExceptionGroup` 形式抛出

```python
from celestialflow.persistence import funnel_scope

with funnel_scope():
    # FallbackSpout 和 LogSpout 已启动
    # 执行业务逻辑...
    ...
# 退出作用域时两个 Spout 已停止
```

## 注意事项

1. **单层作用域**：当前实现不承诺嵌套作用域的复用语义，每次 `funnel_scope` 应独立使用。
2. **异常处理**：进入或退出过程中的异常会被收集到列表中，最终以 `ExceptionGroup` 抛出，不会丢失异常信息。
3. **停止顺序**：先停止 `LogSpout`，再停止 `FallbackSpout`，确保日志尽量完整。
