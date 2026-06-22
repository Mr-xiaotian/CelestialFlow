# BaseObserver

> 📅 最終更新日: 2026/06/22

`BaseObserver` は実行者ライフサイクルオブザーバーの基底クラスであり、`TaskExecutor` が実行中にブロードキャストするイベントインターフェースを定義します。

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

すべてのメソッドはデフォルトで空実装（ABC ではない）。サブクラスが必要に応じてオーバーライドします。

### イベント説明

| イベント | トリガー時期 | パラメータ |
|------|----------|------|
| `on_start` | 実行者が実行を開始 | `_name`: 実行者フルネーム, `_total`: 常に 0（実際のタスク数は `on_tasks_added` で通知） |
| `on_task_success` | 単一タスクが成功 | `count`: 成功数（デフォルト 1） |
| `on_task_fail` | 単一タスクが失敗 | `count`: 失敗数（デフォルト 1） |
| `on_task_duplicate` | 重複タスクを検出 | `count`: 重複数（デフォルト 1） |
| `on_tasks_added` | 新規タスクがキューに追加 | `count`: 新規タスク数 |
| `on_finish` | 実行者が実行を終了 | なし |

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
executor.remove_observer(observer)  # オブザーバーを解除
```

実行者内部では `_notify(method_name, *args, **kwargs)` で登録済みの全オブザーバーにイベントをブロードキャストします。observer リストが空の場合、オブザーバーなしと同等（Null 実装不要）。

## 既存実装

| クラス | 説明 |
|---|------|
| `TaskProgress` | tqdm ベースのプログレスバー表示（`core_progress.md` 参照） |
