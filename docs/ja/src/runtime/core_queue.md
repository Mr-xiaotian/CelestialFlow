# src/celestialflow/runtime/core_queue.py

> 📅 最終更新日: 2026/09/24

`TaskQueue` モジュールは `TaskInQueue` と `TaskOutQueue` の 2 つのクラスを提供し、異なるノード間を接続するパイプとして機能します。マルチプロデューサー・マルチコンシューマーモデルをサポートし、終了シグナル（TerminationSignal）マージ機能を統合しています。

## 概要

- **TaskInQueue**: タスク入力キュー。複数上流からのタスクと終了シグナルを集約します
- **TaskOutQueue**: タスク出力キュー。結果を 1 つ以上の下流キューチャネルにブロードキャストします

両者とも内部で `queue.Queue`（スレッドセーフキュー）をデフォルトバックエンドとして使用します。

---

## TaskInQueue

タスク入力キュー。複数上流からのタスクを受信し、終了シグナルをマージします。

### 初期化

```python
class TaskInQueue[T]:
    def __init__(
        self,
        out_name: str,
        maxsize: int = 0,
    ) -> None:
        """
        :param out_name: 当前节点唯一名称
        :param maxsize: 队列最大容量，默认为 0（无限制）
        """
```

内部属性：

| 属性 | 型 | 説明 |
|------|------|------|
| `out_name` | `str` | 現在のノードの一意名 |
| `queue` | `Queue[TaskEnvelope[T] \| TerminationSignal]` | 基盤となるスレッドセーフキュー |
| `source_names` | `list[str]` | 上流ソース名のリスト |
| `termination_dict` | `dict[str, int]` | 記録済みの終了シグナルソース → ID |

キューは内部で自動作成され、外部から渡す必要はありません。上流ソースは `add_source_name()` で動的に追加します。

### 主要メソッド

#### put

```python
def put(self, item: TaskEnvelope[T] | TerminationSignal) -> None:
    """入队任务或终止信号。"""
```

#### get

```python
def get(self) -> TaskEnvelope[T] | TerminationIdPool:
    """
    出队任务或终止符号 id 池。
    """
```

`get()` は内部で基盤キューを循環消費し、`_process_item()` が非 `None` を返すまで続けます。

終了シグナルマージロジック：

- `"input"` からの終了シグナルを受信 → 即座に `TerminationIdPool(ids=[...])` を返す
- すべての `source_names` からの終了シグナルを受信 → マージして返す
- 一部の上流シグナルのみを受信 → 待機を継続（`_process_item` が `None` を返し、外側のループが継続）
- `TerminationIdPool` 自体（上流でマージ済みのプール）を受信 → 直接返し、上流の合流ロジックを経由しない

#### drain

```python
def drain(self) -> list[TaskEnvelope[T]]:
    """
    清空队列中的所有任务，返回任务列表。
    记录终止信号但不会返回 TerminationIdPool（仅用于同步环境，如 _finish_start）。
    """
```

### 補助メソッド

```python
def add_source_name(self, name: str) -> None:
    """
    添加入队来源名称。

    :param name: 入队来源名称
    :raises DuplicateNodeError: 如果名称已存在
    """
```

内部の終了処理用補助メソッド：

```python
def _record_termination(self, signal: TerminationSignal) -> None:
    """记录入队来源的终止信号；来源不在 source_names ∪ {"input"} 时抛 UnknownNodeError。"""


def _can_merge_termination(self) -> bool:
    """所有 source_names 都已发出终止信号时返回 True。"""


def _merge_termination(self) -> TerminationIdPool:
    """合并所有 source_names 的终止信号；存在遗漏来源时抛 TerminationMergeError。"""
```

> `_merge_termination()` は `source_names` からの終了シグナルのみをマージし、`"input"` が注入する直接終了や、`self.out_name` のマージ後の終了は処理しません。

## TaskOutQueue

タスク出力キュー。複数の下流にタスクをブロードキャストします。

### 初期化

```python
class TaskOutQueue[T]:
    def __init__(
        self,
        in_name: str,
    ) -> None:
        """
        :param in_name: 当前节点唯一名称，用于记录日志
        """
```

出力キューの辞書 `_queues` は初期状態で空であり、`add_queue()` を通じて下流チャネルを動的に追加します。

### 主要メソッド

#### put

```python
def put(self, item: TaskEnvelope[T] | TerminationSignal) -> None:
    """入队任务或终止信号到所有输出队列通道（遍历所有目标逐个转发）。"""
```

#### put_target

```python
def put_target(self, name: str, item: TaskEnvelope[T] | TerminationSignal) -> None:
    """
    入队任务或终止信号到指定的输出队列。

    :param name: 输出队列目标节点名称
    :param item: 要入队的任务或终止信号
    """
```

指定された下流ノードへの定向配信に使用します。

#### get_target_names

```python
def get_target_names(self) -> list[str]:
    """获取所有输出队列的目标节点名称。"""
```

現在登録されているすべての下流チャネルの名前リスト（`_queues` のキー）を返します。

### 補助メソッド

```python
def add_queue(self, name: str, queue: Any) -> None:
    """
    添加一个输出队列到队列列表中。

    :param name: 队列的目标节点名称，用于标识该队列
    :param queue: 要添加的输出队列
    :raises DuplicateNodeError: 如果名称已存在于队列列表中
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
                                        入力が直接終了？    → はい → 即座に返す
                                        それ以外            → 待機継続
```

### マージルール

`TaskInQueue` は全 `source_names` からの終了シグナルを待ち、1 つの `TerminationIdPool` にマージします:

1. `_record_termination` で source の正当性を検証（`source_names ∪ {"input"}` に含まれる必要あり）
2. `"input"` が存在する場合 → 即座に `TerminationIdPool(ids=[...])` を返す
3. `_can_merge_termination()` が True → `_merge_termination()` を呼び出し
4. それ以外は待機継続（`_process_item` が `None` を返し、外側の `get` ループが継続）

---

## 使用例

以下の例は `TaskInQueue` と `TaskOutQueue` の基本的な使用方法を示し、タスクの put/get、終了シグナルのマージ、動的チャネル追加を網羅します。

```python
from queue import Queue as ThreadQueue
from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue
from celestialflow.runtime.util_types import TerminationSignal, TerminationIdPool

# ===== TaskInQueue 使用示例 =====

# 创建输入队列，指定当前节点名称和队列容量
in_queue = TaskInQueue(
    out_name="processor",
    maxsize=0,  # 0 表示无限制
)

# 添加上游来源名称
in_queue.add_source_name("producer1")
in_queue.add_source_name("producer2")

# 上游生产者放入任务
env1 = TaskEnvelope(task=100, id=1)
env2 = TaskEnvelope(task=200, id=2)
in_queue.put(env1)
in_queue.put(env2)

# 下游消费者获取任务
task1 = in_queue.get()
print(f"收到任务: {task1.get_task()}, ID: {task1.get_id()}")

# 动态添加新的上游来源
in_queue.add_source_name("producer3")
print(f"上游来源数: {len(in_queue.source_names)}")

# ===== TaskOutQueue 使用示例 =====

# 创建输出队列（初始为空，后续通过 add_queue 动态添加通道）
out_queue = TaskOutQueue(
    in_name="processor",
)

# 动态添加下游队列通道（注意参数顺序：先名称，后队列）
consumer_q1 = ThreadQueue()
consumer_q2 = ThreadQueue()
out_queue.add_queue("consumer1", consumer_q1)
out_queue.add_queue("consumer2", consumer_q2)

# 广播任务到所有下游
env3 = TaskEnvelope(task="broadcast_msg", id=3)
out_queue.put(env3)

# 验证两个消费者都收到了
print(f"consumer1 收到: {consumer_q1.get().get_task()}")
print(f"consumer2 收到: {consumer_q2.get().get_task()}")

# 定向发送到指定下游
consumer_q3 = ThreadQueue()
out_queue.add_queue("consumer3", consumer_q3)

env4 = TaskEnvelope(task="targeted_msg", id=4)
out_queue.put_target("consumer3", env4)
print(f"consumer3 收到: {consumer_q3.get().get_task()}")

# ===== 终止信号合并 =====

# 新建一个只用于演示合并的输入队列
merge_queue = TaskInQueue(out_name="merger")
merge_queue.add_source_name("producer1")
merge_queue.add_source_name("producer2")

# 两个上游都发送终止信号
merge_queue.put(TerminationSignal(_id=1, source="producer1"))
merge_queue.put(TerminationSignal(_id=2, source="producer2"))

# get() 会自动合并所有上游的终止信号并返回 TerminationIdPool
result = merge_queue.get()

if isinstance(result, TerminationIdPool):
    print(f"收到合并终止信号，包含 IDs: {result.ids}")  # [1, 2]

# ===== drain 清空队列 =====
# 创建新队列并放入残留任务
residual_q = TaskInQueue(
    out_name="drain_test",
)
residual_q.add_source_name("src")
residual_q.put(TaskEnvelope(task="leftover", id=5))

# drain 清空所有剩余任务
leftovers = residual_q.drain()
print(f"残留任务数: {len(leftovers)}")
```

## 注意事項

1. **マルチチャネル**: `TaskOutQueue` は複数の下流キューを管理
2. **ソース管理**: `add_source_name` と `add_queue` はいずれも重複防止（`DuplicateNodeError`）
3. **終了マージ**: `_merge_termination` はソース漏れをチェックし、漏れがある場合は `TerminationMergeError` を送出
4. **drain 特性**: 同期環境（`_finish_start`）でのみ使用され、未消費タスクの収集に使用
