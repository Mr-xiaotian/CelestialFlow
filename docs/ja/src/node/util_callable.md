# validate_executor_func_signature

> 📅 最終更新日: 2026/09/09

`util_callable.py` は実行器関数のシグネチャに対する軽量な検証を提供します。現在公開されているツール関数は `validate_executor_func_signature` のみで、`BaseTaskNode._set_func` がコールバックを登録する際に呼び出します。

## 公開関数

### `validate_executor_func_signature(func)`

```python
def validate_executor_func_signature(func: Callable[..., Any]) -> int:
    """
    実行器関数の引数 kind が要件を満たしているかを検証し、引数の数を返します。
    """
```

動作:

1. `inspect.signature(func)` で引数リストを取得；
2. 各 `Parameter` を走査し、その `kind` が以下のみであることを要求:
   - `inspect.Parameter.POSITIONAL_ONLY`
   - `inspect.Parameter.POSITIONAL_OR_KEYWORD`
3. `VAR_POSITIONAL` / `KEYWORD_ONLY` / `VAR_KEYWORD` / `POSITIONAL_OR_KEYWORD` 以外の型が検出された場合、`CallableParameterKindError`（`celestialflow.runtime.util_errors` 内）を送出；
4. 引数の総数 `len(parameters)` を返します。

> 呼び出し側（`BaseTaskNode._set_func`）が `parameter_count != 1` を再チェックして `ConfigurationError` を送出するため、コールバックは必ず 1 つの位置タスク引数のみを受け取る必要があります。

## パラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `func` | `Callable[..., Any]` | 検証対象のコールバック関数 |

## 戻り値

| 戻り値 | 型 | 説明 |
|------|------|------|
| 引数の数 | `int` | `len(parameters)`。呼び出し側はこれによりコールバックが「単一引数」制約を満たしているかを判断 |

## 例外

| 例外 | トリガー条件 |
|------|---------|
| `CallableParameterKindError` | コールバックに `VAR_POSITIONAL` / `KEYWORD_ONLY` / `VAR_KEYWORD` などの非想定の引数種類が含まれる |

## 使用例

### 合法なコールバック

```python
from celestialflow.node.util_callable import validate_executor_func_signature


def double(x: int) -> int:
    return x * 2


count = validate_executor_func_signature(double)
print(count)  # 1
```

### 非法なコールバック

```python
from celestialflow.node.util_callable import validate_executor_func_signature


def bad(*args, **kwargs):  # VAR_POSITIONAL / VAR_KEYWORD
    return args


try:
    validate_executor_func_signature(bad)
except Exception as exc:
    print(type(exc).__name__, exc)
```

### 完全な流れ：`BaseTaskNode._set_func` との組み合わせ

```python
from celestialflow.node.core_node import BaseTaskNode


def single_arg(x):
    return x


node = BaseTaskNode("Node", func=single_arg, execution_mode="serial")
# _set_func は内部で validate_executor_func_signature(single_arg) を呼び出して 1 を取得し、
# == 1 をチェックした上で最終的に self.func に書き込みます。
```

## 注意事項

1. **戻り値の型は検証しない**：引数の kind と数のみをチェックし、戻り値の型は検証しません。
2. **デフォルト値は検証しない**：`default=` を持つかどうかはチェック結果に影響しません。
3. **型チェッカーとの併用**：`BaseTaskNode` のテンプレート引数 `T / R` とコールバックのシグネチャが一致しない場合は、`TaskExecutor` などにおいて型の一致を別途確認する必要があります。
4. **コルーチンかどうかは検証しない**：コルーチン関数かどうかは `set_execution_mode("async")` と `inspect.iscoroutinefunction` の組み合わせで処理されます。
