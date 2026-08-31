# BaseObserver

> 📅 最終更新日: 2026/08/26

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

    def observer_error(self, method_name: str, exception: Exception) -> None: ...
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
| `observer_error` | オブザーバーコールバックが例外を送出した時 | `method_name`: 例外が発生したコールバック名, `exception`: 捕捉された例外 |

### 自動例外ラッパーメカニズム

`BaseObserver` は `__init_subclass__` を通じて、サブクラス作成時にすべてのオーバーライドコールバック（`on_start`、`on_task_success`、`on_task_fail`、`on_task_duplicate`、`on_tasks_added`、`on_finish`）を自動的にラップします：

- ラッパーはコールバック内で送出されたすべての `Exception` を捕捉し、`observer_error(method_name, exception)` を呼び出した後 `None` を返します。例外はフレームワークに伝播しません。
- 注意：`observer_error` 自体はラップされません。サブクラスでオーバーライドした `observer_error` が例外を送出した場合、それはそのまま外部に伝播します。

### トリガーメカニズム

イベントは統一された `_notify()` で配信されるのではなく、フレームワークが特定の箇所で直接呼び出します：

- `TaskMetrics.on_start(name, total)` → `on_start` をブロードキャスト（`TaskExecutor._prepare_start()` から呼び出され、`total` は常に `0` が渡される）
- `TaskMetrics.add_task_count(count)` → `on_tasks_added` をブロードキャスト
- `TaskMetrics.add_success_count(count)` / `add_fail_count(count)` / `add_duplicate_count(count)` → 対応するコールバックをブロードキャスト
- `TaskMetrics.on_finish()` → `on_finish` をブロードキャスト

オブザーバーは `executor.add_observer(observer)` を通じて登録されます（内部では `TaskMetrics._observers` に格納）。observer リストが空の場合、ブロードキャストループは no-op になります。

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
executor.run([1, 2, 3])
```

### Observer 管理

```python
executor.add_observer(observer)  # オブザーバーを登録
executor.remove_observer(observer)  # オブザーバーを解除
```

## 既存実装

| クラス | 説明 |
|---|------|
| （内蔵実装なし） | ユーザーは必要に応じて `BaseObserver` を継承しカスタムオブザーバーを実装可能 |
