# BaseObserver / CallbackObserver

> 📅 最終更新日: 2026/05/28

`BaseObserver` はエグゼキューターライフサイクルオブザーバーの基底クラスで、`TaskExecutor` が実行中にブロードキャストするイベントインターフェースを定義します。`CallbackObserver` はコールバック関数を通じてイベントを受信する軽量な実装です。

## BaseObserver

```python
class BaseObserver:
    def on_start(self, _name: str, _total: int) -> None: ...
    def on_task_success(self, _count: int = 1) -> None: ...
    def on_task_fail(self, _count: int = 1) -> None: ...
    def on_task_duplicate(self, _count: int = 1) -> None: ...
    def on_tasks_added(self, _count: int) -> None: ...
    def on_finish(self) -> None: ...
```

すべてのメソッドはデフォルトで空の実装（ABC ではない）。サブクラスが必要に応じてオーバーライドします。

### イベント説明

| イベント | トリガータイミング | パラメータ |
|---------|-------------------|-----------|
| `on_start` | エグゼキューター実行開始時 | `_name`: エグゼキューター名、`_total`: 初期タスク総数 |
| `on_task_success` | 単一タスク成功時 | `count`: 成功数（デフォルト 1） |
| `on_task_fail` | 単一タスク失敗時 | `count`: 失敗数（デフォルト 1） |
| `on_task_duplicate` | 重複タスク検出時 | `count`: 重複数（デフォルト 1） |
| `on_tasks_added` | 新タスクがキューに追加された時 | `count`: 新規タスク数 |
| `on_finish` | エグゼキューター実行完了時 | なし |

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

### Observer の管理

```python
executor.add_observer(observer)     # オブザーバーの登録
executor.remove_observer(observer)  # オブザーバーの削除
```

エグゼキューター内部では `_notify(method_name, *args, **kwargs)` を通じて、登録済みのすべてのオブザーバーにイベントをブロードキャストします。observer リストが空の場合、オブザーバーなしと等価です（Null 実装は不要）。

## CallbackObserver

キーワード引数としてコールバック関数を渡すことでイベントを受信する軽量なオブザーバー。サブクラスの定義は不要です。

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
| `CallbackObserver` | コールバック関数式オブザーバー |
