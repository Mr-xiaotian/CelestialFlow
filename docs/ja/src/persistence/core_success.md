# SuccessSpout

> 📅 最終更新日: 2026/05/24

`SuccessSpout` は `BaseSpout` を継承し、成功結果キューを継続的に監視して task-result ペアをキャッシュします。

## アーキテクチャ設計

```mermaid
flowchart LR
    Queue[queue.Queue] -->|デーモンスレッドポーリング| Spout[SuccessSpout._handle_record]
    Spout --> IsEnvelope{record は
TaskEnvelope?}
    IsEnvelope -->|いいえ| Drop[破棄]
    IsEnvelope -->|はい| Extract[result = record.task を抽出
task = record.prev]
    Extract --> Append[success_pairs
リストに追加]
    Append --> Get[get_success_pairs
list[(task, result)] を返す]

    style Queue fill:#fff3e0
    style Spout fill:#e8f5e9
    style IsEnvelope fill:#fff9c4
    style Extract fill:#e3f2fd
    style Append fill:#c8e6c9
    style Get fill:#f3e5f5
```

## 初期化

```python
class SuccessSpout(BaseSpout):
    def __init__(self):
        super().__init__()
        self.success_pairs: list[tuple[Any, Any]] = []
```

## コアメソッド

### get_success_pairs

```python
def get_success_pairs(self) -> list[tuple[Any, Any]]:
    """
    成功したタスクと結果のペアリストを取得する

    :return: [(task, result), ...]
    """
```

## 内部実装

### _handle_record

キューから `TaskEnvelope` を受信し、元のタスク（`record.prev`）と結果（`record.task`）を抽出して `success_pairs` に追加します。

### _before_start

開始前に `success_pairs` をクリアします。

## 使用シーン

成功結果は `SuccessSpout` のキューに送信されます。実行完了後、`get_success_pairs()` ですべての成功した (task, result) ペアを取得できます。

## 使用例

### SuccessSpout と TaskExecutor の連携による成功結果の取得

以下の完全な例は、`SuccessSpout` を使用してすべての成功タスクの `(task, result)` ペアを取得する方法を示します：

```python
import asyncio
from celestialflow import TaskExecutor


def double(x: int) -> int:
    """シンプルな処理関数：入力値を2倍にする"""
    if x < 0:
        raise ValueError(f"負の数は処理できません: {x}")
    return x * 2


async def main():
    # 1. エグゼキューターを作成
    executor = TaskExecutor(
        "倍化処理",
        double,
        execution_mode="thread",
        max_workers=4,
    )

    # 2. エグゼキューターを起動して 0〜9 の数値を処理
    #    SuccessSpout がバックグラウンドで成功結果キューを自動監視
    await executor.start(range(10))

    # 3. すべての成功した (task, result) ペアを取得
    #    executor.get_success_pairs() は実際には SuccessSpout に委譲
    pairs = executor.get_success_pairs()

    # 4. 結果を出力
    print(f"成功裏に {len(pairs)} 個のタスクを処理しました:")
    for task, result in pairs:
        print(f"  入力: {task:>3}  ->  出力: {result}")

    # 期待される出力：
    #   入力:   0  ->  出力: 0
    #   入力:   1  ->  出力: 2
    #   入力:   2  ->  出力: 4
    #   ...
    #   入力:   9  ->  出力: 18


asyncio.run(main())
```

### TaskGraph から全ノードの成功結果を取得

`TaskGraph` のマルチステージタスクグラフを使用する場合、各ステージのエグゼキューターから成功結果を取得できます：

```python
import asyncio
from celestialflow import TaskGraph, TaskStage


def stage_a(x: int) -> str:
    return f"processed-{x}"


def stage_b(s: str) -> dict:
    return {"key": s.upper()}


async def main():
    # マルチステージタスクグラフを作成
    graph = TaskGraph(schedule_mode="staged")
    sa = TaskStage("StageA", stage_a, execution_mode="thread")
    sb = TaskStage("StageB", stage_b, execution_mode="thread")
    graph.set_stages([sa, sb])
    graph.connect([sa], [sb])

    # タスクグラフを起動
    await graph.start_graph({sa.get_tag(): ["apple", "banana", "cherry"]})

    # 各ステージのエグゼキューターから成功結果を取得
    # 注意：実際のプロパティ名は _executor の場合があります。具体的なバージョンを参照してください
    for stage in [sa, sb]:
        pairs = stage.get_success_pairs()
        print(f"ノード {stage.get_tag()}: 成功 {len(pairs)} 個のタスク")
        for task, result in pairs[:2]:  # 最初の2件のみ表示
            print(f"  入力: {task} -> 出力: {result}")


asyncio.run(main())
```
