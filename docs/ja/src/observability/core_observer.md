# BaseObserver / CallbackObserver

> 📅 最終更新日: 2026/05/08

`BaseObserver` はエグゼキューターのライフサイクルオブザーバーの基底クラスで、`TaskExecutor` が実行中にブロードキャストするイベントインターフェースを定義します。`CallbackObserver` はコールバック関数でイベントを受け取る軽量実装です。

## BaseObserver

```python
class BaseObserver:
    def on_start(self, name: str, total: int) -> None: ...
    def on_task_success(self, count: int = 1) -> None: ...
    def on_task_fail(self, count: int = 1) -> None: ...
    def on_task_duplicate(self, count: int = 1) -> None: ...
    def on_tasks_added(self, count: int) -> None: ...
    def on_finish(self) -> None: ...
```

すべてのメソッドはデフォルトで空実装（ABC ではない）。サブクラスは必要に応じてオーバーライドします。

### イベント説明

| イベント | トリガー | パラメータ |
|----------|----------|------------|
| `on_start` | エグゼキューター開始 | `name`: エグゼキューター名, `total`: 初期タスク総数 |
| `on_task_success` | タスク成功 | `count`: 成功数（デフォルト 1） |
| `on_task_fail` | タスク失敗 | `count`: 失敗数（デフォルト 1） |
| `on_task_duplicate` | 重複タスク検出 | `count`: 重複数（デフォルト 1） |
| `on_tasks_added` | 新タスクがキューに追加 | `count`: 新規タスク数 |
| `on_finish` | エグゼキューター終了 | なし |

### 使用方法

```python
from celestialflow import BaseObserver, TaskExecutor

class MyObserver(BaseObserver):
    def on_task_success(self, count=1):
        print(f"成功: {count}")

    def on_task_fail(self, count=1):
        print(f"失敗: {count}")

executor = TaskExecutor("Test", my_func)
executor.add_observer(MyObserver())
executor.start(tasks)
```

### Observer 管理

```python
executor.add_observer(observer)     # オブザーバーを登録
executor.remove_observer(observer)  # オブザーバーを削除
```

内部的に、エグゼキューターは `_notify(method_name, *args, **kwargs)` を通じて登録済みの全オブザーバーにイベントをブロードキャストします。observer リストが空の場合、オーバーヘッドはありません（Null 実装不要）。

## CallbackObserver

キーワード引数でコールバック関数を受け取る軽量オブザーバー。サブクラス化不要。

```python
class CallbackObserver(BaseObserver):
    def __init__(self, **callbacks):
        for name, fn in callbacks.items():
            setattr(self, name, fn)
```

### 使用方法

```python
from celestialflow import CallbackObserver, TaskExecutor

observer = CallbackObserver(
    on_task_success=lambda count=1: print(f"成功: {count}"),
    on_finish=lambda: print("完了"),
)

executor = TaskExecutor("Test", my_func)
executor.add_observer(observer)
executor.start(tasks)
```

関心のあるイベントのみオーバーライドし、残りは `BaseObserver` のデフォルト空実装を使用します。

## 既存の実装

| クラス | 説明 |
|--------|------|
| `TaskProgress` | tqdm ベースのプログレスバー表示（`core_progress.md` 参照） |
| `CallbackObserver` | コールバック式オブザーバー |
