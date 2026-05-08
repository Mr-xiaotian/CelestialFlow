# TaskProgress

> 📅 最終更新日: 2026/05/08

`TaskProgress` は `BaseObserver` を継承し、tqdm ベースのタスク進捗可視化を提供します。

## 機能

- **動的更新**: `on_tasks_added` でタスク総数を動的に増加、ストリーミングやタスク分裂シナリオに対応。
- **ライフサイクル管理**: `on_start` でプログレスバーを作成、`on_finish` で閉じる。
- **イベント駆動**: `on_task_success/fail/duplicate` で進捗を更新。

## インターフェース

```python
class TaskProgress(BaseObserver):
    def on_start(self, name: str, total: int) -> None:
        # tqdm プログレスバーを作成
    def on_task_success(self, count: int = 1) -> None:
        # 進捗を更新
    def on_task_fail(self, count: int = 1) -> None:
        # 進捗を更新
    def on_task_duplicate(self, count: int = 1) -> None:
        # 進捗を更新
    def on_tasks_added(self, count: int) -> None:
        # タスク総数を増加しリフレッシュ
    def on_finish(self) -> None:
        # プログレスバーを閉じる
```

## 使用方法

```python
from celestialflow import TaskExecutor, TaskProgress

executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)
```

プログレスバーが不要な場合は observer を追加しなければよく、Null 実装は不要です。
