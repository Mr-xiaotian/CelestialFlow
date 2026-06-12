# StageTypes

> 📅 Last Updated: 2026/06/11

`stage/util_types.py` defines type aliases for the Stage module, providing convenient references for generic Stages.

## Core Types

### AnyTaskStage

A generic wildcard alias for `TaskStage`, used for type annotations when specific input/output types do not need to be specified.

```python
from typing import Any

from .core_stage import TaskStage

type AnyTaskStage = TaskStage[Any, Any]
```

| Attribute | Description |
|------|------|
| Full Name | `TaskStage[Any, Any]` |
| Purpose | Wildcard placeholder in type annotations, suitable when specific data types are irrelevant |
| Definition Location | `stage/util_types.py` (imports `TaskStage` from `stage/core_stage.py`) |

## Usage Examples

### Wildcard Usage in Type Annotations

```python
from celestialflow.stage.util_types import AnyTaskStage
from celestialflow.stage import TaskStage

# When you need to declare a variable that can accept any type of Stage
def register_stage(stage: AnyTaskStage) -> None:
    print(f"Registered Stage: {stage.name}")

# Can pass TaskStage with any generic parameters
int_stage: TaskStage[int, int] = TaskStage("A", func=lambda x: x * 2)
str_stage: TaskStage[str, str] = TaskStage("B", func=lambda x: x.upper())

register_stage(int_stage)  # Passes type checking
register_stage(str_stage)  # Passes type checking
```

### Storing Stages of Different Types in a Container

```python
from celestialflow.stage.util_types import AnyTaskStage
from celestialflow.stage import TaskStage

stages: list[AnyTaskStage] = []

stages.append(TaskStage("A", func=lambda x: x * 2))          # TaskStage[int, int]
stages.append(TaskStage("B", func=lambda x: x.upper()))      # TaskStage[str, str]
stages.append(TaskStage("C", func=lambda x: len(x)))         # TaskStage[str, int]

# No need to manually annotate complex generic types
for s in stages:
    print(f"  {s.name}: {s}")
```

## Notes

- `AnyTaskStage` is only used for type annotations and does not change runtime behavior. In practice, type checkers (such as Pyright / mypy) will expand it to `TaskStage[Any, Any]`.
- This type alias requires Python 3.12+ `type` statement syntax.
