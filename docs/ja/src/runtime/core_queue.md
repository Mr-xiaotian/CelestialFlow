# TaskQueue

> 📅 最終更新日: 2026/04/24

`TaskQueue` モジュールは `TaskInQueue` と `TaskOutQueue` の2つのクラスを提供し、異なる Stage 間のパイプラインを接続します。マルチプロデューサー・マルチコンシューマーモデルをサポートし、ログ記録と監視機能を統合しています。

## 概要

- **TaskInQueue**: タスク入力キュー、上流からタスクを受信するために使用
- **TaskOutQueue**: タスク出力キュー、下流にタスクを送信するために使用

両方とも複数のバックエンドをサポート：`queue.Queue` (Thread)、`multiprocessing.Queue` (Process)、`asyncio.Queue` (Async)。

---

## TaskInQueue

タスク入力キュー。複数の上流からのタスクを受信しマージするために使用します。

### 初期化

```python
class TaskInQueue:
    def __init__(
        self,
        queue: ThreadQueue | MPQueue | AsyncQueue,
        queue_tags: list[str],
        out_tag: str,
        log_inlet: "LogInlet",
    ):
        """
        タスク入力キューを初期化する。

        :param queue: キューオブジェクト
        :param queue_tags: 上流キュータグのリスト
        :param out_tag: 現在のノードのタグ
        :param log_inlet: ログレコーダー
        """
```

### 主要メソッド

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal):
    """
    タスクまたは終了シグナルをエンキューする。

    :param item: エンキューするタスクまたは終了シグナル
    """
```

#### get

```python
def get(self) -> TaskEnvelope | TerminationIdPool:
    """
    タスクまたは終了シグナルプールをデキューする。

    :return: タスクエンベロープまたは終了シグナル ID プール
    """
```

**終了シグナルのマージロジック**：
- `"input"` からの終了シグナルを受信した場合、即座に返す
- すべての `queue_tags` からの終了シグナルを受信した場合、マージして返す

#### drain

```python
def drain(self) -> list[TaskEnvelope]:
    """
    キュー内のすべてのタスクを取り出し、タスクリストを返す。
    終了シグナルの状態は記録するが、TerminationIdPool は返さない。

    :return: すべてのタスクを含むリスト
    """
```

### 補助メソッド

```python
def add_source_tag(self, tag: str):
    """
    上流キュータグを追加する。

    :param tag: 上流キュータグ
    :raises ValueError: タグが既に存在する場合
    """
```

---

## TaskOutQueue

タスク出力キュー。複数の下流にタスクを送信するために使用します。

### 初期化

```python
class TaskOutQueue:
    def __init__(
        self,
        queue_list: list[ThreadQueue] | list[MPQueue] | list[AsyncQueue],
        queue_tags: list[str],
        in_tag: str,
        log_inlet: "LogInlet",
    ):
        """
        タスク出力キューを初期化する。

        :param queue_list: 出力キューのリスト
        :param queue_tags: キュータグのリスト
        :param in_tag: 現在のノードのタグ
        :param log_inlet: ログレコーダー
        :raises ValueError: キューリストとタグリストの長さが一致しない場合
        """
```

### 主要メソッド

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal):
    """
    タスクまたは終了シグナルをすべての出力チャネルにエンキューする。
    """
```

#### put_target

```python
def put_target(self, item: TaskEnvelope | TerminationSignal, tag: str):
    """
    タスクまたは終了シグナルを指定タグの出力チャネルにエンキューする。

    :param item: エンキューするタスクまたは終了シグナル
    :param tag: 出力キュータグ
    """
```

`TaskRouter` の方向指定配信でよく使用されます。

#### put_channel

```python
def put_channel(self, item: TaskEnvelope | TerminationSignal, idx: int):
    """
    タスクまたは終了シグナルを指定インデックスの出力チャネルにエンキューする。

    :param item: エンキューするタスクまたは終了シグナル
    :param idx: 出力チャネルのインデックス
    """
```

### 補助メソッド

```python
def add_queue(self, queue: ThreadQueue | MPQueue | AsyncQueue, tag: str):
    """
    出力キューをキューリストに追加する。

    :param queue: 追加する出力キュー
    :param tag: キュータグ
    :raises ValueError: タグが既に存在する場合
    """
```

---

## 終了シグナル機構

### シグナルの流れ

```
上流ノード ──TaskOutQueue──> キュー ──TaskInQueue──> 現在のノード
    │                              │
    └── TerminationSignal ──────> termination_dict
                                        │
                                        v
                               TerminationIdPool にマージ
```

### マージルール

`TaskInQueue` はすべての `queue_tags` からの終了シグナルを待ち、1つの `TerminationIdPool` にマージします：

1. 終了シグナルを受信したら、`termination_dict` に記録
2. すべての上流が終了シグナルを送信済みか確認
3. すべて受信した場合、`TerminationIdPool` にマージして返す
4. そうでなければ待機を続行

特殊処理：
- `"input"` タグの終了シグナルは即座に返す

---

## 使用例

### TaskGraph での使用

```python
from celestialflow.runtime import TaskInQueue, TaskOutQueue
from multiprocessing import Queue as MPQueue

# 入力キュー
in_queue = TaskInQueue(
    queue=MPQueue(),
    queue_tags=["upstream_stage"],
    out_tag="current_stage",
    log_inlet=log_inlet,
)

# 出力キュー
out_queue = TaskOutQueue(
    queue_list=[MPQueue()],
    queue_tags=["downstream_stage"],
    in_tag="current_stage",
    log_inlet=log_inlet,
)
```

### 動的な下流の追加

```python
# 新しい下流キューを追加
out_queue.add_queue(new_queue, "new_downstream")
```

### 終了シグナルの処理

```python
# タスクを取得
item = in_queue.get()

if isinstance(item, TaskEnvelope):
    # タスクを処理
    result = process(item.task)
    out_queue.put(TaskEnvelope.wrap(result, result_id))
elif isinstance(item, TerminationIdPool):
    # すべての上流が終了済み、下流に終了シグナルを送信
    out_queue.put(TerminationSignal())
```

---

## 注意事項

1. **マルチチャネル**: 1つの `TaskOutQueue` で複数の下流キューを管理可能
2. **ログ記録**: すべてのエンキュー/デキュー操作がログに記録される
3. **スレッドセーフ**: 内部でキューを使用して実装されており、マルチスレッド/マルチプロセスアクセスをサポート
4. **終了マージ**: 複数上流の終了シグナルのマージを正しく処理
