# TaskQueue

> 📅 最終更新日: 2026/04/22

`TaskQueue` モジュールは、異なる Stage を接続するパイプラインとして機能する `TaskInQueue` と `TaskOutQueue` の2つのクラスを提供します。マルチプロデューサー、マルチコンシューマーモデルをサポートし、ロギングと監視機能が統合されています。

## 概要

- **TaskInQueue**: 上流からタスクを受け取るためのタスク入力キュー
- **TaskOutQueue**: 下流にタスクを送信するためのタスク出力キュー

両方とも複数のバックエンドをサポートしています: `queue.Queue` (Thread)、`multiprocessing.Queue` (Process)、`asyncio.Queue` (Async)。

---

## TaskInQueue

複数の上流ソースからタスクを受け取り、マージするためのタスク入力キューです。

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
        タスク入力キューを初期化します。

        :param queue: キューオブジェクト
        :param queue_tags: 上流キュータグのリスト
        :param out_tag: 現在のノードタグ
        :param log_inlet: ロガー
        """
```

### 主要メソッド

#### put / put_async

```python
def put(self, item: TaskEnvelope | TerminationSignal):
    """
    タスクまたは終了シグナルをエンキューします。

    :param item: エンキューするタスクまたは終了シグナル
    """

async def put_async(self, item: TaskEnvelope | TerminationSignal):
    """
    タスクまたは終了シグナルを非同期でエンキューします。
    """
```

#### get / get_async

```python
def get(self) -> TaskEnvelope | TerminationIdPool:
    """
    タスクまたは終了シグナルプールをデキューします。

    :return: タスクエンベロープまたは終了シグナル ID プール
    """

async def get_async(self) -> TaskEnvelope | TerminationIdPool:
    """
    タスクまたは終了シグナルプールを非同期でデキューします。
    """
```

**終了シグナルのマージロジック**:
- `"input"` からの終了シグナルを受信した場合、即座に返します
- 現在のノードタグ（`out_tag`）からの終了シグナルを受信した場合、即座に返します
- すべての `queue_tags` からの終了シグナルを受信した場合、マージして返します

#### drain

```python
def drain(self) -> list[TaskEnvelope]:
    """
    キュー内のすべてのタスクをドレインし、タスクリストを返します。
    終了シグナルの状態は記録しますが、TerminationIdPool は返しません。

    :return: すべてのタスクを含むリスト
    """
```

### 補助メソッド

```python
def add_source_tag(self, tag: str):
    """
    上流キュータグを追加します。

    :param tag: 上流キュータグ
    :raises ValueError: タグが既に存在する場合
    """

def reset(self):
    """
    タスク入力キューの状態をリセットします（終了シグナル記録をクリアします）。
    """
```

---

## TaskOutQueue

複数の下流ターゲットにタスクを送信するためのタスク出力キューです。

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
        タスク出力キューを初期化します。

        :param queue_list: 出力キューのリスト
        :param queue_tags: キュータグのリスト
        :param in_tag: 現在のノードタグ
        :param log_inlet: ロガー
        :raises ValueError: キューリストとタグリストの長さが異なる場合
        """
```

### 主要メソッド

#### put / put_async

```python
def put(self, item: TaskEnvelope | TerminationSignal):
    """
    すべての出力チャネルにタスクまたは終了シグナルをエンキューします。
    """

async def put_async(self, item: TaskEnvelope | TerminationSignal):
    """
    すべての出力チャネルにタスクまたは終了シグナルを非同期でエンキューします。
    """
```

#### put_target

```python
def put_target(self, item: TaskEnvelope | TerminationSignal, tag: str):
    """
    指定されたタグの出力チャネルにタスクまたは終了シグナルをエンキューします。

    :param item: エンキューするタスクまたは終了シグナル
    :param tag: 出力キュータグ
    """
```

`TaskRouter` のターゲットルーティングでよく使用されます。

#### put_channel / put_channel_async

```python
def put_channel(self, item: TaskEnvelope | TerminationSignal, idx: int):
    """
    指定されたインデックスの出力チャネルにタスクまたは終了シグナルをエンキューします。

    :param item: エンキューするタスクまたは終了シグナル
    :param idx: 出力チャネルインデックス
    """

async def put_channel_async(self, item: TaskEnvelope | TerminationSignal, idx: int):
    """
    指定されたインデックスの出力チャネルにタスクまたは終了シグナルを非同期でエンキューします。
    """
```

### 補助メソッド

```python
def add_queue(self, queue: ThreadQueue | MPQueue | AsyncQueue, tag: str):
    """
    出力キューをキューリストに追加します。

    :param queue: 追加する出力キュー
    :param tag: キュータグ
    :raises ValueError: タグが既に存在する場合
    """
```

---

## 終了シグナルメカニズム

### シグナルフロー

```
上流ノード ──TaskOutQueue──> キュー ──TaskInQueue──> 現在のノード
    │                              │
    └── TerminationSignal ──────> termination_dict
                                        │
                                        v
                               TerminationIdPool にマージ
```

### マージルール

`TaskInQueue` はすべての `queue_tags` からの終了シグナルを待機し、単一の `TerminationIdPool` にマージします:

1. 終了シグナルを受信すると、`termination_dict` に記録します
2. すべての上流ソースが終了シグナルを送信したかチェックします
3. すべて受信した場合、`TerminationIdPool` にマージして返します
4. そうでなければ、待機を続けます

特別な処理:
- `"input"` タグの終了シグナルは即座に返します
- 現在のノードタグ（`out_tag`）の終了シグナルは即座に返します

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

### 下流の動的追加

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
    # すべての上流が終了したので、下流に終了シグナルを送信
    out_queue.put(TerminationSignal())
```

---

## 注意事項

1. **マルチチャネル**: 1つの `TaskOutQueue` で複数の下流キューを管理できます
2. **ロギング**: すべてのエンキュー/デキュー操作がログに記録されます
3. **非同期サポート**: `put_async`、`get_async` などの非同期メソッドを提供します
4. **スレッドセーフティ**: 内部的にマルチスレッド/マルチプロセスアクセスをサポートするキュー実装を使用しています
5. **終了マージ**: 複数の上流ソースからの終了シグナルのマージを正しく処理します
