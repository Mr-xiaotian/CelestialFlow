# node/util_types.py

> 📅 最后更新日期: 2026/09/09

`util_types.py` 为 `node` 模块提供节点层特有的类型别名。当前仅定义一个 `AnyTaskNode` 类型别名，供 `TaskGraph` 等上层结构以"任意节点"的形式引用节点对象。

> 运行时用到的 `TaskEnvelope` / `TaskInQueue` / `TaskOutQueue` / `TaskMetrics` / `TerminationSignal` / `CTreeEvent` / `ValueWrapper` 等核心类型并不在本文件，而是分别由 `celestialflow.runtime` 与 `celestialflow.runtime.util_types` 提供，详见 `docs/zh-CN/src/runtime/__init__.md`。

## 公开类型

### `AnyTaskNode`

```python
from typing import Any
from .core_node import BaseTaskNode

type AnyTaskNode = BaseTaskNode[Any, Any]
```

含义：

- 退化为"任意输入 / 任意输出"的 `BaseTaskNode`；
- 仅在静态类型层面使用，运行期不影响实际行为；
- 主要用于 `TaskGraph` 维护的 `node_dict`、公共方法 `connect` / `set_nodes` 等"不在意具体类型"的位置。

## 典型用法

```python
from celestialflow.node.util_types import AnyTaskNode


def collect_names(nodes: list[AnyTaskNode]) -> list[str]:
    return [n.get_name() for n in nodes]
```

> `AnyTaskNode` 仅做类型擦除，不会引入额外运行时开销；调用方仍可通过 `isinstance(n, TaskExecutor | TaskSplitter | TaskRouter)` 做精细化分支。

## 注意事项

1. **类型别名，不参与导入列表**：该文件没有 `__all__`，不需要从 `celestialflow.node.util_types` 显式 `import`；可通过 `celestialflow.node` 间接访问。
2. **范围限定**：`AnyTaskNode` 不应当用于"具体节点"位置；比如 `TaskExecutor[T, R]` 的入参仍应使用泛型版本，避免破坏静态推断。
3. **与 `runtime` 模块的类型协作**：`BaseTaskNode` 内部直接使用 `runtime` 模块的 `TaskEnvelope` / `TaskInQueue` / `TaskOutQueue` / `TaskMetrics` / `ValueWrapper` / `CTreeEvent` / `TerminationSignal`，这些类型的具体说明见对应文档。
