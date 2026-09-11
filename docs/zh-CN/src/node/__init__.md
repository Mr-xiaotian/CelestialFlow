# node/__init__.py

> 📅 最后更新日期: 2026/09/09

## 作用

`celestialflow.node` 包对外暴露节点层的全部公共 API。它从 `core_nodes` 模块重新导出 `TaskExecutor`、`TaskSplitter` 与 `TaskRouter`，为任务图提供"执行、拆分、路由"三类可直接作为图节点使用的流水线组件。

> 该模块的 docstring 仍保留历史名称 "CelestialFlow 阶段模块"，可继续保留。

## 公开导出符号（`__all__`）

```python
from celestialflow.node import (
    TaskExecutor,  # 通用任务执行器
    TaskSplitter,  # 1→N 任务拆分器
    TaskRouter,  # 条件路由器
)
```

完整 `__all__`：

```python
__all__ = [
    "TaskExecutor",
    "TaskRouter",
    "TaskSplitter",
]
```

> ⚠️ `BaseTaskNode` 与 `TaskDispatch` **不**在 `__all__` 中，属于内部抽象，由 `TaskExecutor` / `TaskSplitter` / `TaskRouter` 在构造时内部使用，外部代码不应直接依赖。

## 三个核心节点类

| 导出符号 | 源模块 | 父类 | 用途 |
|---------|-------|------|------|
| `TaskExecutor` | `core_nodes` | `BaseTaskNode[T, R]` | 通用任务执行器，把单个输入映射为单个结果 |
| `TaskSplitter` | `core_nodes` | `BaseTaskNode[Iterable[TItem], Iterable[RItem]]` | 拆分器，将单个任务拆为多个子任务（1→N） |
| `TaskRouter` | `core_nodes` | `BaseTaskNode[T, tuple[str, T]]` | 路由器，根据用户自定义的 `router` 函数将任务分发到不同下游 |

## 使用示例

### TaskExecutor — 独立执行一组任务

```python
from celestialflow.node import TaskExecutor


def double(x: int) -> int:
    return x * 2


executor = TaskExecutor("Doubler", func=double, execution_mode="serial")
executor.run([1, 2, 3, 4, 5])

for task, result in executor.get_success_pairs():
    print(f"{task} -> {result}")
```

### TaskSplitter — 把一个集合拆成多条子任务

```python
from celestialflow.node import TaskSplitter

# 把字符串拆成单个字符
splitter = TaskSplitter("CharSplitter")

# 配合下游 TaskGraph:
# graph.connect([splitter], [downstream])
# splitter.run([["abc", "de"]])
```

### TaskRouter — 按条件路由到不同下游

```python
from celestialflow.node import TaskRouter


def by_length(text: str) -> str:
    return "LongPath" if len(text) > 5 else "ShortPath"


router = TaskRouter("LengthRouter", router=by_length)
# graph.connect([router], [long_node, short_node])
```

## 与其它模块的关联

- **`core_node`**: 定义基类 `BaseTaskNode` 与内部调度器 `TaskDispatch`，是所有节点的运行时骨架。
- **`core_nodes`**: 提供三个公共节点类。
- **`runtime`**: 节点依赖 `TaskEnvelope` / `TaskInQueue` / `TaskOutQueue` / `TaskMetrics` 进行队列与指标通信。
- **`observability`**: 通过 `BaseObserver` 上报执行进度。
- **`persistence`**: 通过 `LifecycleInlet` / `LogInlet` 落盘任务生命周期与日志。

## 注意事项

1. **基类非公共 API**：`BaseTaskNode` 与 `TaskDispatch` 不会出现在 `__all__` 中。如需自定义节点行为，请继承 `TaskExecutor` 并覆写 `process_task_success` / `get_binding_counter`。
2. **入口层一致性**：从 `celestialflow` 顶层包入口（`docs/zh-CN/src/__init__.md`）也可直接 `import` 上述三个符号。
3. **生命周期**：所有节点 `start()` / `start_async()` 是一次性调用，执行完毕后应新建实例而不是复位复用。
