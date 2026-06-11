# StageTypes

> 📅 最后更新日期: 2026/06/11

`stage/util_types.py` 定义 Stage 模块的类型别名，提供泛型 Stage 的便捷引用。

## 核心类型

### AnyTaskStage

`TaskStage` 的泛型通配别名，用于无需指定具体输入输出类型时的类型标注。

```python
from typing import Any

from .core_stage import TaskStage

type AnyTaskStage = TaskStage[Any, Any]
```

| 属性 | 说明 |
|------|------|
| 全称 | `TaskStage[Any, Any]` |
| 用途 | 类型注解中的通配占位，适用于不关心具体数据类型的场景 |
| 定义位置 | `stage/util_types.py`（从 `stage/core_stage.py` 导入 `TaskStage`） |

## 使用示例

### 类型注解中的通配用法

```python
from celestialflow.stage.util_types import AnyTaskStage
from celestialflow.stage import TaskStage

# 当需要声明一个可以接收任意类型 Stage 的变量时
def register_stage(stage: AnyTaskStage) -> None:
    print(f"已注册 Stage: {stage.name}")

# 可以传入任意泛型参数的 TaskStage
int_stage: TaskStage[int, int] = TaskStage("A", func=lambda x: x * 2)
str_stage: TaskStage[str, str] = TaskStage("B", func=lambda x: x.upper())

register_stage(int_stage)  # 通过类型检查
register_stage(str_stage)  # 通过类型检查
```

### 容器中存放多种类型的 Stage

```python
from celestialflow.stage.util_types import AnyTaskStage
from celestialflow.stage import TaskStage

stages: list[AnyTaskStage] = []

stages.append(TaskStage("A", func=lambda x: x * 2))          # TaskStage[int, int]
stages.append(TaskStage("B", func=lambda x: x.upper()))      # TaskStage[str, str]
stages.append(TaskStage("C", func=lambda x: len(x)))         # TaskStage[str, int]

# 无需手动标注复杂的泛型类型
for s in stages:
    print(f"  {s.name}: {s}")
```

## 注意事项

- `AnyTaskStage` 仅用于类型标注，不改变运行时行为。实际使用时类型检查器（如 Pyright / mypy）会将其展开为 `TaskStage[Any, Any]`。
- 该类型别名依赖 Python 3.12+ 的 `type` 语句语法。
