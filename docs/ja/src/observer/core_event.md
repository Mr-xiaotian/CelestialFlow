# src/celestialflow/observer/core_event.py

> 📅 最終更新日: 2026/10/09

`core_event.py` は観測者体系における**すべてのイベント型**を定義します。これらは観測者コールバックの引数として、タスク / ノード / タスクグラフのライフサイクルにおけるさまざまな変化を記述します。すべてのイベントは `frozen=True, slots=True` の読み取り専用 `dataclass` です。

## イベント一覧

| イベント | フィールド | トリガー時期 |
|------|------|----------|
| `NodeStartEvent` | `node`、`execution_mode`、`max_workers` | ノード起動 |
| `NodeEndEvent` | `node`、`execution_mode`、`max_workers`、`elapsed` | ノード終了 |
| `TaskInputEvent` | `node`、`task`、`task_repr`、`input_id`、`from_node` | タスクがノードの入力キューに入る |
| `TaskSuccessEvent` | `node`、`task`、`task_repr`、`result`、`result_repr`、`elapsed`、`task_id`、`success_id` | タスクの成功処理 |
| `TaskFailEvent` | `node`、`task`、`task_repr`、`exception`、`task_id`、`error_id` | タスクの最終失敗 |
| `TaskSkipEvent` | `node`、`task`、`task_repr`、`task_id`、`skip_id` | タスクのスキップ |
| `TaskRetryEvent` | `node`、`task`、`task_repr`、`exception`、`task_id`、`retry_times` | タスク失敗だがリトライをトリガー |
| `TerminationInputEvent` | `node`、`termination_id` | 終了シグナルが入力キューに入る |
| `TerminationMergeEvent` | `node`、`parent_ids`、`termination_id` | 複数ソースの終了シグナルがマージされる |
| `WorkerCrashEvent` | `node`、`exception` | ワーカースレッド / コルーチンがフォールバック層で未処理例外を捕捉 |
| `GraphStartEvent` | `graph`、`graph_mode`、`start_time`、`class_name`、`is_dag`、`nodes`、`edges`、`source_nodes`、`node_meta` | タスクグラフ起動 |
| `GraphEndEvent` | `graph`、`elapsed` | タスクグラフ終了 |

## フィールドの説明

### 共通フィールド

- `node`：ノード名。イベントの属するノードを識別します。
- `task`：元のタスクデータ（`Any`）、`task_repr` はその可読文字列表現。

### イベント ID フィールド

- `input_id`：現在の入力イベント ID。
- `task_id`：タスク入力イベント ID（`TaskInputEvent.input_id` と対応）。
- `success_id` / `error_id` / `skip_id`：成功 / エラー / スキップイベントそれぞれのイベント ID。
- `termination_id`：終了シグナルイベント ID。
- `parent_ids`：マージに参加した終了シグナルイベント ID のリスト。

### タスクの発生源

- `from_node`：上流の発生源ノード名。`None` は外部から直接注入されたことを表します。このフィールドは `MetricsObserver` が外部注入と上流配信を区別する根拠です。

### グラフ元情報（`GraphStartEvent`）

- `graph`：タスクグラフ名。
- `graph_mode`：タスクグラフの実行モード。
- `start_time`：タスクグラフの起動時間。
- `class_name`：タスクグラフクラス名。
- `is_dag`：DAG タスクグラフかどうか。
- `nodes`：タスクグラフのノード名リスト。
- `edges`：タスクグラフの辺隣接リスト（`{from_name: [to_name, ...]}`）。
- `source_nodes`：ソースノード名リスト。
- `node_meta`：各ノードの構築期のメタ情報。

## コード例

```python
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TaskSuccessEvent:
    node: str
    task: Any
    task_repr: str
    result: Any
    result_repr: str
    elapsed: float
    task_id: int
    success_id: int
```

すべてのイベントは `frozen=True, slots=True` を使用します。つまり不変（構築後のフィールド変更不可、ハッシュ化可能）かつ `__slots__` によるメモリ節約を実現します。

## 使用例

```python
from celestialflow.observer import (
    Observer,
    ObserverHub,
    TaskFailEvent,
    TaskSuccessEvent,
    WorkerCrashEvent,
)


class MyObserver(Observer):
    def on_task_success(self, event: TaskSuccessEvent) -> None:
        print(f"{event.node} 成功: {event.result_repr}")

    def on_task_fail(self, event: TaskFailEvent) -> None:
        print(f"{event.node} 失敗: {event.exception}")

    def on_worker_crash(self, event: WorkerCrashEvent) -> None:
        print(f"{event.node} ワーカークラッシュ: {event.exception}")


hub = ObserverHub()
hub.add_observer(MyObserver())
```

## 注意事項

1. **読み取り専用イベント**：イベントはすべて不変 `dataclass` であり、観測者がイベント内部のフィールドを変更してはなりません。
2. **フレームワークが構築**：イベントはノード / タスクグラフが対応するタイミングで構築し `hub.on_*()` を呼び出します。一般に手動構築は不要です。
3. **旧「カウント型コールバック」は廃止**：イベントオブジェクトが旧版 `BaseObserver` の `on_task_success(count)` などの基本パラメータコールバックを置き換え、より豊かなコンテキストを保持できます。