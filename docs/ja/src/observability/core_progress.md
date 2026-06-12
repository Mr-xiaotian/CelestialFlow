# TaskProgress

> 📅 最終更新日: 2026/06/11

`TaskProgress` は `BaseObserver` を継承し、`tqdm` ベースでタスク進捗の可視化表示を提供します。

## 機能

- **動的更新**: `on_tasks_added` を通じて総タスク数の動的増加をサポートし、ストリーミングタスクやタスク分割シナリオに対応。
- **ライフサイクル管理**: `on_start` 時にプログレスバーを作成し、`on_finish` 時に閉じる。
- **イベント駆動**: `on_task_success/fail/duplicate` を通じて進捗を更新。

## インターフェース

```python
class TaskProgress(BaseObserver):
    _bar: tqdm[Any]

    def on_start(self, name: str, total: int) -> None:
        # tqdm プログレスバーを作成
    def on_task_success(self, count: int = 1) -> None:
        # 進捗を更新
    def on_task_fail(self, count: int = 1) -> None:
        # 進捗を更新
    def on_task_duplicate(self, count: int = 1) -> None:
        # 進捗を更新
    def on_tasks_added(self, count: int) -> None:
        # 総タスク数を増加してリフレッシュ
    def on_finish(self) -> None:
        # プログレスバーを閉じる
```

## 使用

```python
from celestialflow import TaskExecutor, TaskProgress

executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)
```

プログレスバーが不要な場合は observer を追加しなければよく、Null 実装は不要です。

## 使用例

### TaskProgress と TaskExecutor の併用

```python
from celestialflow import TaskExecutor, TaskProgress


def slow_task(n: int) -> int:
    """時間のかかるタスクをシミュレート"""
    import time
    time.sleep(0.05)
    return n * n


# 1. 実行者を作成、スレッドモードで実行
executor = TaskExecutor(
    "平方計算",
    slow_task,
    execution_mode="thread",
    max_workers=10,
)

# 2. プログレスバーオブザーバーを追加
executor.add_observer(TaskProgress())

# 3. 実行者を起動して 100 個のタスクを処理
executor.start(range(100))
print("すべてのタスクが完了しました！")
```

### 動的タスク追加時のプログレスバー

実行中にタスクが動的に増加する場合（タスク分割シナリオなど）、`TaskProgress` は自動的にプログレスバーの総量を拡張します：

```python
from celestialflow import TaskExecutor, TaskProgress


def dynamic_task(n: int) -> list[int]:
    """入力値に応じて動的に新規タスクを生成"""
    if n % 10 == 0:
        return [n + 1, n + 2]
    return [n]


executor = TaskExecutor("動的タスク", dynamic_task, execution_mode="thread")

progress = TaskProgress()
executor.add_observer(progress)

# 初期 20 タスク、実行中に動的増加
executor.start(range(20))
```
