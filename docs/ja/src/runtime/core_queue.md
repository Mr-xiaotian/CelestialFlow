# TaskQueue

> 📅 最終更新日: 2026/05/09

`TaskQueue` モジュールは、異なる Stage を接続するパイプラインとして使用される `TaskInQueue` と `TaskOutQueue` の2つのクラスを提供します。マルチプロデューサー、マルチコンシューマーモデルをサポートし、ログ記録と監視機能を統合しています。

## 概要

- **TaskInQueue**: タスク入力キュー、上流からタスクを受信
- **TaskOutQueue**: タスク出力キュー、下流へタスクを送信

両方とも複数のバックエンドをサポート：`queue.Queue`（Thread）、`asyncio.Queue`（Async）。

---

## TaskInQueue

複数の上流からタスクを受信・マージするタスク入力キュー。

### 初期化

```python
class TaskInQueue:
    def __init__(
        self,
        queue: ThreadQueue | AsyncQueue,
        queue_tags: list[str],
        out_tag: str,
        log_inlet: "LogInlet",
    ):
        """
        タスク入力キューを初期化します。

        :param queue: キューオブジェクト
        :param queue_tags: 上流キュータグリスト
        :param out_tag: 現在のノードタグ
        :param log_inlet: ロガー
        """
```

### 主要メソッド

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal):
    """
    タスクまたは終了シグナルをエンキューします。

    :param item: エンキューするタスクまたは終了シグナル
    """
```

#### get

```python
def get(self) -> TaskEnvelope | TerminationIdPool:
    """
    タスクまたは終了シグナルプールをデキューします。

    :return: タスクエンベロープまたは終了シグナル ID プール
    """
```

**終了シグナルマージロジック**：
- `"input"` からの終了シグナルを受信した場合、即座に返却
- すべての `queue_tags` からの終了シグナルを受信した場合、マージして返却

#### drain

```python
def drain(self) -> list[TaskEnvelope]:
    """
    キュー内のすべてのタスクをドレインし、リストとして返します。
    終了シグナルの状態を記録しますが、TerminationIdPool は返しません。

    :return: すべてのタスクを含むリスト
    """
```

### ヘルパーメソッド

```python
def add_source_tag(self, tag: str):
    """
    上流キュータグを追加します。

    :param tag: 上流キュータグ
    :raises ValueError: タグが既に存在する場合
    """
```

---

## TaskOutQueue

複数の下流ノードにタスクを送信するタスク出力キュー。

### 初期化

```python
class TaskOutQueue:
    def __init__(
        self,
        queue_list: list[ThreadQueue] | list[AsyncQueue],
        queue_tags: list[str],
        in_tag: str,
        log_inlet: "LogInlet",
    ):
        """
        タスク出力キューを初期化します。

        :param queue_list: 出力キューリスト
        :param queue_tags: キュータグリスト
        :param in_tag: 現在のノードタグ
        :param log_inlet: ロガー
        :raises ValueError: キューリストとタグリストの長さが一致しない場合
        """
```

### 主要メソッド

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal):
    """
    すべての出力チャネルにタスクまたは終了シグナルをエンキューします。
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

`TaskRouter` のターゲット配信によく使用されます。

#### put_channel

```python
def put_channel(self, item: TaskEnvelope | TerminationSignal, idx: int):
    """
    指定されたインデックスの出力チャネルにタスクまたは終了シグナルをエンキューします。

    :param item: エンキューするタスクまたは終了シグナル
    :param idx: 出力チャネルインデックス
    """
```

### ヘルパーメソッド

```python
def add_queue(self, queue: ThreadQueue | AsyncQueue, tag: str):
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

`TaskInQueue` はすべての `queue_tags` からの終了シグナルを待ち、単一の `TerminationIdPool` にマージします：

1. 終了シグナルを受信したら `termination_dict` に記録
2. すべての上流が終了シグナルを送信したか確認
3. すべて受信済みなら `TerminationIdPool` にマージして返却
4. そうでなければ待機を継続

特殊処理：
- `"input"` タグの終了シグナルは即座に返却

---

## 使用例

### TaskGraph での使用

```python
from celestialflow.runtime import TaskInQueue, TaskOutQueue
from queue import Queue as ThreadQueue

# 入力キュー
in_queue = TaskInQueue(
    queue=ThreadQueue(),
    queue_tags=["upstream_stage"],
    out_tag="current_stage",
    log_inlet=log_inlet,
)

# 出力キュー
out_queue = TaskOutQueue(
    queue_list=[ThreadQueue()],
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
    result = process(item.get_task())
    out_queue.put(TaskEnvelope(result, id=result_id, source="stage_tag"))
elif isinstance(item, TerminationIdPool):
    # すべての上流が終了、下流に終了シグナルを送信
    out_queue.put(TerminationSignal())
```

---

## 注意事項

1. **マルチチャネル**: 1つの `TaskOutQueue` で複数の下流キューを管理可能
2. **ログ記録**: すべてのエンキュー/デキュー操作がログに記録される
3. **スレッドセーフ**: 内部でマルチスレッドアクセスをサポートするキュー実装を使用
4. **終了マージ**: 複数の上流からの終了シグナルのマージを適切に処理
