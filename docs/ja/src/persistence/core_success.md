# SuccessSpout

> 📅 最終更新日: 2026/06/11

`SuccessSpout` は `BaseSpout` を継承し、成功結果キューを継続的に監視して task-result ペアをキャッシュします。

## アーキテクチャ設計

```mermaid
flowchart LR
    Queue[queue.Queue] -->|デーモンスレッドポーリング| Spout[SuccessSpout._handle_record]
    Spout --> IsEnvelope{record は<br/>TaskEnvelope?}
    IsEnvelope -->|いいえ| Drop[破棄]
    IsEnvelope -->|はい| Extract[result = record.task<br/>task = record.prev を抽出]
    Extract --> Append[success_pairs リストに<br/>追加]
    Append --> Get[get_success_pairs<br/>list[(task, result)] を返す]
```

## 初期化

```python
class SuccessSpout[T, R](BaseSpout):
    def __init__(self):
        super().__init__()
        self.success_pairs: list[tuple[T, R]] = []
```

## コアメソッド

### get_success_pairs

```python
def get_success_pairs(self) -> list[tuple[T, R]]:
    """
    成功タスクと結果のペアリストを取得

    :return: [(task, result), ...]
    """
```

## 内部実装

### _handle_record

キューから `TaskEnvelope` を受信し、型チェック後に元のタスク（`record.prev`）と結果（`record.task`）を抽出して `success_pairs` に追加します。`TaskEnvelope` 型でないレコードは直接破棄されます。

### _before_start

起動前に `success_pairs` をクリアし、毎回の実行結果がクリーンであることを保証します。

## 使用シナリオ

成功結果は `SuccessSpout` のキューに送信され、実行終了後に `get_success_pairs()` で成功したすべての (task, result) ペアを取得できます。`TaskExecutor` の `get_success_pairs()` は内部の `SuccessSpout` に委譲します。

## 使用例

### SuccessSpout と TaskExecutor の連携による成功結果の取得

```python
from celestialflow import TaskExecutor


def double(x: int) -> int:
    """シンプルな処理関数：入力値を 2 倍にする"""
    if x < 0:
        raise ValueError(f"負の数は処理できません: {x}")
    return x * 2


# 1. 実行者を作成
executor = TaskExecutor(
    "倍加処理",
    double,
    execution_mode="thread",
    max_workers=4,
)

# 2. 実行者を起動して 0~9 の数字を処理
#    SuccessSpout はバックグラウンドで成功結果キューを自動監視
executor.start(range(10))

# 3. 成功したすべての (task, result) ペアを取得
pairs = executor.get_success_pairs()

print(f"{len(pairs)} 個のタスクを成功処理しました:")
for task, result in pairs:
    print(f"  入力: {task:>3}  ->  出力: {result}")
```

### TaskGraph から全ノードの成功結果を取得

`TaskGraph` でマルチステージタスクグラフを使用する場合、各ステージの実行者から成功結果を取得できます：

```python
from celestialflow import TaskGraph, TaskStage


def stage_a(x: int) -> str:
    return f"processed-{x}"


def stage_b(s: str) -> dict:
    return {"key": s.upper()}


# マルチステージタスクグラフを作成
graph = TaskGraph(schedule_mode="staged")
sa = TaskStage("StageA", stage_a, execution_mode="thread")
sb = TaskStage("StageB", stage_b, execution_mode="thread")
graph.set_stages([sa, sb])
graph.connect([sa], [sb])

# タスクグラフを起動
graph.start_graph({sa.get_name(): ["apple", "banana", "cherry"]})

# 各ステージの実行者から成功結果を取得
for stage in [sa, sb]:
    pairs = stage.get_success_pairs()
    print(f"ノード {stage.get_name()}: {len(pairs)} 個のタスクが成功")
    for task, result in pairs[:2]:
        print(f"  入力: {task} -> 出力: {result}")
```

> **変更点**：以前の例では `stage.get_tag()` と `await graph.start_graph()` を使用していましたが、現在のソースコードでは Stage は `get_name()` を一意識別子として使用し、`start_graph()` は同期メソッドです。
