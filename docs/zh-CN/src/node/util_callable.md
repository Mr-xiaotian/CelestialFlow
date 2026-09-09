# node/util_callable.py

> 📅 最后更新日期: 2026/09/09

`util_callable.py` 提供对执行器函数签名的轻量级校验。当前仅暴露一个工具函数 `validate_executor_func_signature`，供 `BaseTaskNode._set_func` 在注册回调时调用。

## 公开函数

### `validate_executor_func_signature(func)`

```python
def validate_executor_func_signature(func: Callable[..., Any]) -> int:
    """
    验证执行器函数的参数 kind 是否符合要求，并返回参数数量。
    """
```

行为：

1. 用 `inspect.signature(func)` 取出参数列表；
2. 遍历每个 `Parameter`，要求其 `kind` 只能是：
   - `inspect.Parameter.POSITIONAL_ONLY`
   - `inspect.Parameter.POSITIONAL_OR_KEYWORD`
3. 若发现 `VAR_POSITIONAL` / `KEYWORD_ONLY` / `VAR_KEYWORD` / `POSITIONAL_OR_KEYWORD` 之外的类型，抛 `CallableParameterKindError`（位于 `celestialflow.runtime.util_errors`）；
4. 返回参数总数 `len(parameters)`。

> 调用方（`BaseTaskNode._set_func`）会再检查 `parameter_count != 1` 并抛 `ConfigurationError`，从而保证回调只接受一个位置任务参数。

## 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `func` | `Callable[..., Any]` | 待校验的回调函数 |

## 返回值

| 返回 | 类型 | 说明 |
|------|------|------|
| 参数数量 | `int` | `len(parameters)`，调用方据此判断回调是否符合"单参数"约束 |

## 异常

| 异常 | 触发条件 |
|------|---------|
| `CallableParameterKindError` | 回调中存在 `VAR_POSITIONAL` / `KEYWORD_ONLY` / `VAR_KEYWORD` 等非预期参数种类 |

## 使用示例

### 合法回调

```python
from celestialflow.node.util_callable import validate_executor_func_signature


def double(x: int) -> int:
    return x * 2


count = validate_executor_func_signature(double)
print(count)  # 1
```

### 非法回调

```python
from celestialflow.node.util_callable import validate_executor_func_signature


def bad(*args, **kwargs):  # VAR_POSITIONAL / VAR_KEYWORD
    return args


try:
    validate_executor_func_signature(bad)
except Exception as exc:
    print(type(exc).__name__, exc)
```

### 完整流程：与 `BaseTaskNode._set_func` 的配合

```python
from celestialflow.node.core_node import BaseTaskNode


def single_arg(x):
    return x


node = BaseTaskNode("Node", func=single_arg, execution_mode="serial")
# _set_func 内部会先调用 validate_executor_func_signature(single_arg) 拿到 1，
# 再校验 == 1，最终写入 self.func。
```

## 注意事项

1. **不校验返回值类型**：仅检查参数 kind 与数量，不验证返回类型。
2. **不校验默认值**：是否带 `default=` 不影响校验结果。
3. **类型化检查器配合**：若 `BaseTaskNode` 模板参数 `T / R` 与回调签名不一致，仍需在 `TaskExecutor` 等位置自行确保类型一致。
4. **不校验协程**：是否协程函数由 `set_execution_mode("async")` 配合 `inspect.iscoroutinefunction` 处理。
