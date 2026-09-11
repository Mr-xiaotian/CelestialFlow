# node/util_callable.py

> 📅 Last Updated: 2026/09/09

`util_callable.py` provides lightweight validation of executor function signatures. It currently exposes a single utility function, `validate_executor_func_signature`, which `BaseTaskNode._set_func` calls when registering a callback.

## Public Functions

### `validate_executor_func_signature(func)`

```python
def validate_executor_func_signature(func: Callable[..., Any]) -> int:
    """
    Validate that the parameter kinds of an executor function conform to the requirements, and return the parameter count.
    """
```

Behavior:

1. Use `inspect.signature(func)` to obtain the parameter list;
2. Iterate over every `Parameter`, requiring its `kind` to be only:
   - `inspect.Parameter.POSITIONAL_ONLY`
   - `inspect.Parameter.POSITIONAL_OR_KEYWORD`
3. If a type other than `VAR_POSITIONAL` / `KEYWORD_ONLY` / `VAR_KEYWORD` / `POSITIONAL_OR_KEYWORD` is found, raise `CallableParameterKindError` (defined in `celestialflow.runtime.util_errors`);
4. Return the total parameter count `len(parameters)`.

> The caller (`BaseTaskNode._set_func`) further checks `parameter_count != 1` and raises `ConfigurationError`, thereby guaranteeing that the callback accepts only one positional task argument.

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `func` | `Callable[..., Any]` | The callback function to validate |

## Return Value

| Return | Type | Description |
|--------|------|-------------|
| Parameter count | `int` | `len(parameters)`, used by the caller to determine whether the callback satisfies the "single argument" constraint |

## Exceptions

| Exception | Trigger Condition |
|-----------|-------------------|
| `CallableParameterKindError` | The callback contains unexpected parameter kinds such as `VAR_POSITIONAL` / `KEYWORD_ONLY` / `VAR_KEYWORD` |

## Usage Examples

### A Valid Callback

```python
from celestialflow.node.util_callable import validate_executor_func_signature


def double(x: int) -> int:
    return x * 2


count = validate_executor_func_signature(double)
print(count)  # 1
```

### An Invalid Callback

```python
from celestialflow.node.util_callable import validate_executor_func_signature


def bad(*args, **kwargs):  # VAR_POSITIONAL / VAR_KEYWORD
    return args


try:
    validate_executor_func_signature(bad)
except Exception as exc:
    print(type(exc).__name__, exc)
```

### Full Flow: Cooperation with `BaseTaskNode._set_func`

```python
from celestialflow.node.core_node import BaseTaskNode


def single_arg(x):
    return x


node = BaseTaskNode("Node", func=single_arg, execution_mode="serial")
# Internally, _set_func first calls validate_executor_func_signature(single_arg) to get 1,
# then checks == 1, and finally writes self.func.
```

## Notes

1. **Does not validate the return type**: it only checks parameter kind and count, not the return type.
2. **Does not validate default values**: whether or not `default=` is provided has no effect on the validation result.
3. **Cooperation with type checkers**: if the `BaseTaskNode` template parameters `T / R` do not match the callback signature, you still need to ensure type consistency yourself at the `TaskExecutor` level.
4. **Does not validate coroutines**: whether the function is a coroutine is handled by `set_execution_mode("async")` together with `inspect.iscoroutinefunction`.
