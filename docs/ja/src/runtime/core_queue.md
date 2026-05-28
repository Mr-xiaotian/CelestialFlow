# TaskQueue

> 📅 最終更新日: 2026/05/28

`TaskQueue` モジュールは、異なる Stage を接続するパイプラインとして使用される `TaskInQueue` と `TaskOutQueue` の2つのクラスを提供します。マルチプロデューサー、マルチコンシューマーモデルをサポートし、ログ記録と終了シグナルマージ機能を統合しています。

## 概要

- **TaskInQueue**: タスク入力キュー。複数の上流ソースからのタスクと終了シグナルを集約
- **TaskOutQueue**: タスク出力キュー。1つ以上の下流キューチャネルに結果をブロードキャスト

両方とも複数のキューバックエンドをサポート：`queue.Queue`（Thread）、`asyncio.Queue`（Async）。

---

## TaskInQueue

複数の上流ソースからのタスクの受信、重複排除、およびマージを行うタスク入力キュー。

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
        :param source_names: 上流ノード名リスト
        :param out_name: 現在のノードの一意の名前
        """
```

### 主要メソッド

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal) -> None:
    """
    タスクまたは終了シグナルをエンキュー。エンキューログを記録。
    """
```

#### get

```python
def get(self) -> TaskEnvelope | TerminationIdPool:
    """
    タスクまたは終了シグナル ID プールをデキュー。

    終了シグナルマージロジック：
    - "input" からの終了シグナル → 即座に TerminationIdPool を返す
    - 全 source_names からの終了シグナルを受信 → マージして返す
    - 一部の上流シグナルのみ受信 → 待機を継続（None を返し、内部でループリトライ）
    """
```

#### drain

```python
def drain(self) -> list[TaskEnvelope]:
    """
    キュー内の全タスクを排出し、タスクリストを返す。
    終了シグナルを記録するが TerminationIdPool は返さない（_finalize_nodes などの同期環境でのみ使用）。
    """
```

### ヘルパーメソッド

```python
def add_source_name(self, name: str) -> None:
    """
    上流ソース名を動的に追加。

    :param name: 上流ノード名
    :raises DuplicateNodeError: 名前が既に存在する場合
    """
```

## TaskOutQueue

複数の下流ノードにタスクをブロードキャストするタスク出力キュー。

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
        :param target_names: 下流ノード名リスト（queue_list の長さと一致する必要あり）
        :param in_name: 現在のノードの一意の名前
        :raises ConfigurationError: 2つのリストの長さが一致しない場合
        """
```

### 主要メソッド

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal) -> None:
    """全出力チャネルにタスクまたは終了シグナルをエンキュー。"""
```

#### put_target

```python
def put_target(self, item: TaskEnvelope | TerminationSignal, name: str) -> None:
    """
    指定された名前の出力チャネルにエンキュー。

    :param name: 下流 Stage 名
    """
```

特定の下流 Stage へのターゲット配信に使用。

#### put_channel

```python
def put_channel(self, item: TaskEnvelope | TerminationSignal, idx: int) -> None:
    """
    指定されたインデックスの出力チャネルにエンキュー。

    :param idx: 出力チャネルインデックス
    """
```

### ヘルパーメソッド

```python
def add_queue(self, queue: Any, name: str) -> None:
    """
    出力キューを動的に追加。

    :param queue: キューインスタンス
    :param name: ターゲットノード名
    :raises DuplicateNodeError: 名前が既に存在する場合
    """
```

---

## 終了シグナルメカニズム

### シグナルフロー

```
上流ノード → out_queue.put(TerminationSignal) → キュー
                                                        ↓
                                                in_queue.get()
                                                        ↓
                                            termination_dict[source] = id
                                                        ↓
                                            全ソース集結？→ はい → merge → TerminationIdPool
                                            入力から直接終了？→ はい → 即座に返す
                                            それ以外 → 待機継続
```

### マージルール

`TaskInQueue` はすべての `source_names` からの終了シグナルを待ち、単一の `TerminationIdPool` にマージします：

1. `_record_termination` でソースの正当性を検証（`source_names ∪ {"input"}` に含まれる必要あり）
2. `"input"` が存在する場合 → 即座に `TerminationIdPool(ids=[...])` を返す
3. `_can_merge_termination()` が True → `_merge_termination()` を呼び出す
4. それ以外は待機を継続（`_deal_get_item` が `None` を返し、外側の `get` ループが継続）

---

## 使用例

以下に、タスクの put/get、終了シグナルマージ、動的チャネル追加を含む `TaskInQueue` と `TaskOutQueue` の基本使用例を示します。

```python
from queue import Queue as ThreadQueue
from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue
from celestialflow.runtime.util_types import TerminationSignal

# ===== TaskInQueue 使用例 =====

# 2つの上流（"producer1"、"producer2"）からのタスクを集約する入力キューを作成
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

# 新しい上流ソースを動的に追加
in_queue.add_source_name("producer3")
print(f"上流ソース数: {len(in_queue.source_names)}")

# ===== TaskOutQueue 使用例 =====

# 2つの下流にブロードキャストする出力キューを作成
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

# 特定の下流にターゲット送信
consumer_q3 = ThreadQueue()
out_queue.add_queue(consumer_q3, "consumer3")

env4 = TaskEnvelope(task="targeted_msg", id=4, source="processor")
out_queue.put_target(env4, "consumer3")
print(f"consumer3 受信: {consumer_q3.get().get_task()}")

# ===== 終了シグナルマージ =====

# 両方の上流が終了シグナルを送信
in_queue.put(TerminationSignal(_id=1, source="producer1"))
in_queue.put(TerminationSignal(_id=2, source="producer2"))

# get() が全上流の終了シグナルを自動的にマージし TerminationIdPool を返す
result = in_queue.get()
from celestialflow.runtime.util_types import TerminationIdPool
if isinstance(result, TerminationIdPool):
    print(f"マージされた終了シグナル受信、IDs: {result.ids}")

# ===== drain でキューをクリア =====
# 新しいキューを作成し残存タスクを投入
residual_q = TaskInQueue(
    queue=ThreadQueue(),
    source_names=["src"],
    out_name="drain_test",
)
residual_q.put(TaskEnvelope(task="leftover", id=5, source="src"))

# drain で全残存タスクをクリア
leftovers = residual_q.drain()
print(f"残存タスク数: {len(leftovers)}")
```

## 注意事項

1. **マルチチャネル**: `TaskOutQueue` は複数の下流キューを管理
2. **ログ記録**: すべての put/get 操作がログに記録。例外時は `put_item_error` を記録
3. **ソース管理**: `add_source_name` と `add_queue` は重複を防止（`DuplicateNodeError`）
4. **終了マージ**: `_merge_termination` は不足ソースをチェックし、不足時は `TerminationMergeError` を発生
5. **drain の特性**: 同期環境（`_finalize_nodes`）でのみ使用され、未消費タスクの収集に利用
