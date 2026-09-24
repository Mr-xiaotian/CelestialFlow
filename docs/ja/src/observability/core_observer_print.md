# src/celestialflow/observability/core_observer_print.py

> 📅 最終更新日: 2026/09/24

`core_observer_print.py` はすぐに使えるコンソールオブザーバー `PrintObserver` を提供します。これは `BaseObserver` を継承し、タスクの実行進捗（起動、追加、成功、失敗、重複、終了）を `print` で標準出力に出力します。ローカルデバッグやサンプルデモに便利です。

## PrintObserver

```python
from threading import Lock

from celestialflow.runtime.util_types import ValueWrapper
from celestialflow.observability.core_observer import BaseObserver


class PrintObserver(BaseObserver):
    def __init__(self, name: str) -> None: ...

    def on_start(self) -> None: ...
    def on_finish(self) -> None: ...
    def on_task_added(self, count: int) -> None: ...
    def on_task_success(self, count: int = 1) -> None: ...
    def on_task_fail(self, count: int = 1) -> None: ...
    def on_task_duplicate(self, count: int = 1) -> None: ...
```

### 構築パラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `name` | `str` | **必須**。出力プレフィックスで、異なるノードのオブザーバーを区別するために使用（`[name] ...` の形） |

コンストラクタ内部では `Lock` を 1 つ作成し、4 つのスレッドセーフな `ValueWrapper` カウンタを初期化します:

| 属性 | 型 | 説明 |
|------|------|------|
| `total` | `ValueWrapper` | 注入済みタスクの総数。`on_task_added` で加算 |
| `succeeded` | `ValueWrapper` | 成功タスク数。`on_task_success` で加算 |
| `failed` | `ValueWrapper` | 失敗タスク数。`on_task_fail` で加算 |
| `duplicated` | `ValueWrapper` | 重複タスク数。`on_task_duplicate` で加算 |
| `name` | `str` | 保存された出力プレフィックス |

### コールバックの動作

| コールバック | 動作 |
|------|------|
| `on_start()` | `[{name}] start total={total}` を出力 |
| `on_finish()` | `[{name}] finish total=..., succeeded=..., failed=..., duplicated=...` を出力 |
| `on_task_added(count)` | `total += count`、`[{name}] total=...(+count)` を出力 |
| `on_task_success(count=1)` | `succeeded += count`、`[{name}] succeeded=...(+count), total=...` を出力 |
| `on_task_fail(count=1)` | `failed += count`、`[{name}] failed=...(+count), total=...` を出力 |
| `on_task_duplicate(count=1)` | `duplicated += count`、`[{name}] duplicated=...(+count), total=...` を出力 |

> すべてのカウントは `ValueWrapper` を通じて共有ロックの保護下で読み書きされるため、`thread` / `async` 実行モードでも安全に呼び出せます。

## 使用例

### ノードに直接登録

```python
from celestialflow import TaskExecutor, PrintObserver


def double(x: int) -> int:
    return x * 2


executor = TaskExecutor("Doubler", double, execution_mode="thread", max_workers=4)
executor.add_observer(PrintObserver("Doubler"))
executor.run([1, 2, 3])
# 控制台输出形如：
# [Doubler] total=3(+3)
# [Doubler] start total=3
# [Doubler] succeeded=1(+1), total=3
# ...
# [Doubler] finish total=3, succeeded=3, failed=0, duplicated=0
```

### 最終統計を読み取る

```python
from celestialflow import TaskExecutor, PrintObserver


def may_fail(x: int) -> int:
    if x % 2 == 0:
        raise ValueError(f"bad {x}")
    return x


executor = TaskExecutor("Odd", may_fail)
observer = PrintObserver("Odd")
executor.add_observer(observer)
executor.run([1, 2, 3, 4])

print(observer.succeeded.get(), observer.failed.get())
```

## 注意事項

1. **`name` は必須パラメータ**：コンストラクタ署名は `__init__(self, name: str)` に変更され、引数なしの構築はできなくなりました。
2. **`total` の基準**：`total` は `put_task` / `run` 経由で注入されたタスクのみを集計します。グラフモードでは上流ノードから下流へ送られたタスクは `on_task_added` を発火しないため、非ソースノードの `total` は実際の処理量より小さくなります。
3. **コールバック順序**：`run()` は先に全タスクを注入してから実行を開始するため、`on_task_added` が `on_start` より先に到達することがあります。
4. **例外分離**：コールバック内の例外は `BaseObserver.__init_subclass__` でラップされた後 `observer_error()` に委譲され、ノード実行を中断しません。
