# TaskQueue

> 📅 最終更新日: 2026/06/11

`TaskQueue` モジュールは `TaskInQueue` と `TaskOutQueue` の 2 つのクラスを提供し、異なる Stage 間を接続するパイプとして機能します。マルチプロデューサー・マルチコンシューマーモデルをサポートし、終了シグナル（TerminationSignal）マージ機能を統合しています。

## 概要

- **TaskInQueue**: タスク入力キュー。複数上流からのタスクと終了シグナルを集約します
- **TaskOutQueue**: タスク出力キュー。結果を 1 つ以上の下流キューチャネルにブロードキャストします

両者とも複数のキューバックエンドをサポートします: `queue.Queue`（Thread）、`asyncio.Queue`（Async）。

---

## TaskInQueue

タスク入力キュー。複数上流からのタスクの受信、重複排除、マージを行います。

### 初期化

```python
class TaskInQueue:
    def __init__(
        self,
        queue: Any,
        source_names: list[str],
        out_name: str,
    ):
        """
        :param queue: キューオブジェクト
        :param source_names: 上流ノード名のリスト
        :param out_name: 現在のノードの一意名
        """
```

### 主要メソッド

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal) -> None:
    """
    タスクまたは終了シグナルをエンキューします。
    """
```

#### get

```python
def get(self) -> TaskEnvelope | TerminationIdPool:
    """
    タスクまたは終了シグナル ID プールをデキューします。

    終了シグナルマージロジック:
    - "input" からの終了シグナルを受信 → 即座に TerminationIdPool を返す
    - 全 source_names からの終了シグナルを受信 → マージして返す
    - 一部の上流シグナルのみ → 待機継続（None を返し、内部ループでリトライ）
    """
```

#### drain

```python
def drain(self) -> list[TaskEnvelope]:
    """
    キュー内の全タスクをクリアし、タスクリストを返します。
    終了シグナルは記録しますが TerminationIdPool は返しません（同期環境でのみ使用、例: _finalize_nodes）。
    """
```

### 補助メソッド

```python
def add_source_name(self, name: str) -> None:
    """
    上流ソース名を動的に追加します。

    :param name: 上流ノード名
    :raises DuplicateNodeError: 名前が既存の場合
    """
```

## TaskOutQueue

タスク出力キュー。複数の下流にタスクをブロードキャストします。

### 初期化

```python
class TaskOutQueue:
    def __init__(
        self,
        queue_list: list[Any],
        target_names: list[str],
        in_name: str,
    ):
        """
        :param queue_list: 出力キューリスト
        :param target_names: 下流ノード名リスト（長さは queue_list と一致必須）
        :param in_name: 現在のノードの一意名
        :raises ConfigurationError: 2 つのリストの長さが一致しない場合
        """
```

### 主要メソッド

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal) -> None:
    """タスクまたは終了シグナルを全出力チャネルにエンキューします。"""
```

#### put_target

```python
def put_target(self, item: TaskEnvelope | TerminationSignal, name: str) -> None:
    """
    指定された名前の出力チャネルにエンキューします。

    :param name: 下流 Stage 名
    """
```

指定された下流 Stage への定向配信に使用します。

#### put_channel

```python
def put_channel(self, item: TaskEnvelope | TerminationSignal, idx: int) -> None:
    """
    指定されたインデックスの出力チャネルにエンキューします。

    :param idx: 出力チャネルインデックス
    """
```

### 補助メソッド

```python
def add_queue(self, queue: Any, name: str) -> None:
    """
    出力キューを動的に追加します。

    :param queue: キューインスタンス
    :param name: ターゲットノード名
    :raises DuplicateNodeError: 名前が既存の場合
    """
```

---

## 終了シグナル機構

### シグナルフロー

```
上流ノード → out_queue.put(TerminationSignal) → キュー
                                                    ↓
                                            in_queue.get()
                                                    ↓
                                        termination_dict[source] = id
                                                    ↓
                                        全 source が揃った？→ はい → merge → TerminationIdPool
                                        入力が直接終了？  → はい → 即座に返す
                                        それ以外         → 待機継続
```

### マージルール

`TaskInQueue` は全 `source_names` からの終了シグナルを待ち、1 つの `TerminationIdPool` にマージします:

1. `_record_termination` で source の正当性を検証（`source_names ∪ {"input"}` に含まれる必要あり）
2. `"input"` が存在する場合 → 即座に `TerminationIdPool(ids=[...])` を返す
3. `_can_merge_termination()` が True → `_merge_termination()` を呼び出し
4. それ以外は待機継続（`_deal_get_item` が `None` を返し、外側の `get` ループが継続）

---

## 使用例

以下の例は `TaskInQueue` と `TaskOutQueue` の基本的な使用方法を示し、タスクの put/get、終了シグナルのマージ、動的チャネル追加を網羅します。

```python
from queue import Queue as ThreadQueue
from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue
from celestialflow.runtime.util_types import TerminationSignal

# ===== TaskInQueue 使用例 =====

# 入力キューを作成。2 つの上流（"producer1", "producer2"）からのタスクを集約
in_queue = TaskInQueue(
    queue=ThreadQueue(),
    source_names=["producer1", "producer2"],
    out_name="processor",
)

# 上流プロデューサーがタスクを投入
env1 = TaskEnvelope(task=100, id=1, source="producer1")
env2 = TaskEnvelope(task=200, id=2, source="producer2")
in_queue.put(env1)
in_queue.put(env2)

# 下流コンシューマーがタスクを取得
task1 = in_queue.get()
print(f"受信タスク: {task1.get_task()}, ソース: {task1.source}")

# 新しい上流ソースを動的追加
in_queue.add_source_name("producer3")
print(f"上流ソース数: {len(in_queue.source_names)}")

# ===== TaskOutQueue 使用例 =====

# 出力キューを作成。2 つの下流にブロードキャスト
consumer_q1 = ThreadQueue()
consumer_q2 = ThreadQueue()

out_queue = TaskOutQueue(
    queue_list=[consumer_q1, consumer_q2],
    target_names=["consumer1", "consumer2"],
    in_name="processor",
)

# 全下流にタスクをブロードキャスト
env3 = TaskEnvelope(task="broadcast_msg", id=3, source="processor")
out_queue.put(env3)

# 両方のコンシューマーが受信したことを確認
print(f"consumer1 受信: {consumer_q1.get().get_task()}")
print(f"consumer2 受信: {consumer_q2.get().get_task()}")

# 指定下流への定向送信
consumer_q3 = ThreadQueue()
out_queue.add_queue(consumer_q3, "consumer3")

env4 = TaskEnvelope(task="targeted_msg", id=4, source="processor")
out_queue.put_target(env4, "consumer3")
print(f"consumer3 受信: {consumer_q3.get().get_task()}")

# ===== 終了シグナルマージ =====

# 両方の上流が終了シグナルを送信
in_queue.put(TerminationSignal(_id=1, source="producer1"))
in_queue.put(TerminationSignal(_id=2, source="producer2"))

# get() は全上流の終了シグナルを自動マージし TerminationIdPool を返す
result = in_queue.get()
from celestialflow.runtime.util_types import TerminationIdPool
if isinstance(result, TerminationIdPool):
    print(f"マージ済み終了シグナル受信、ID 一覧: {result.ids}")

# ===== drain でキューをクリア =====
# 新規キューを作成し残留タスクを投入
residual_q = TaskInQueue(
    queue=ThreadQueue(),
    source_names=["src"],
    out_name="drain_test",
)
residual_q.put(TaskEnvelope(task="leftover", id=5, source="src"))

# drain で全残留タスクをクリア
leftovers = residual_q.drain()
print(f"残留タスク数: {len(leftovers)}")
```

## 注意事項

1. **マルチチャネル**: `TaskOutQueue` は複数の下流キューを管理します
2. **ソース管理**: `add_source_name` と `add_queue` はいずれも重複防止（`DuplicateNodeError`）
3. **終了マージ**: `_merge_termination` はソース漏れをチェックし、漏れがある場合は `TerminationMergeError` を送出
4. **drain 特性**: 同期環境（`_finalize_nodes`）でのみ使用され、未消費タスクの収集に使用
