# Clone

> 📅 最終更新日: 2026/06/18

`utils/util_clone.py` は実行器、ノード、タスクグラフのクローン機能を提供し、パフォーマンステストと設定再利用に使用します。

## 設計目的

パフォーマンステストでは、同じタスクグラフ設定を複数回実行する必要がありますが、各実行で内部状態が変更されます。クローン機能は完全に独立したコピーを作成し、状態汚染を防止します。

## 主要関数

### clone_executor

`TaskExecutor` インスタンスをクローンします。

```python
def clone_executor(executor: TaskExecutor) -> TaskExecutor:
    """
    実行器をクローンします。

    :param executor: クローンする実行器
    :return: 新しい実行器インスタンス
    """
```

コピーされる属性：
- `name`: 実行器名
- `func`: タスク関数
- `execution_mode`: 実行モード
- `max_workers`: 並行制限
- `max_retries`: 最大リトライ回数
- `max_info`: ログ情報の最大長
- `enable_duplicate_check`: 重複チェックスイッチ
- `persist_result`: 結果永続化スイッチ
- `log_level`: ログレベル
- `retry_exceptions`: リトライ可能例外リスト

### clone_stage

`TaskStage` インスタンスをクローンします。

```python
def clone_stage(stage: TaskStage) -> TaskStage:
    """
    ノードをクローンします。

    :param stage: クローンするノード
    :return: 新しいノードインスタンス
    """
```

`TaskExecutor` の属性に加えて、以下もコピーされます：
- `stage_mode`: ノードモード

### clone_graph

`TaskGraph` インスタンスをクローンします。

```python
def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    タスクグラフをクローンします。

    :param graph: クローンするタスクグラフ
    :return: 新しいタスクグラフインスタンス
    """
```

クローンフロー：
1. 元のグラフの全ノードを走査（BFS）
2. 各ノードをクローンしてマッピングを確立
3. ノード間の接続関係を再構築
4. グラフ設定をコピー（schedule_mode, log_level）
5. CelestialTree と Reporter 設定をコピー

## 使用例

### 実行器のクローン

```python
from celestialflow import TaskExecutor
from celestialflow.utils.util_clone import clone_executor

# 元の実行器を作成
executor = TaskExecutor(
    "Processor",
    process,
    execution_mode="thread",
    max_workers=10,
    max_retries=3,
)

# 実行器をクローン
cloned = clone_executor(executor)

# 2つの実行器が独立して実行
executor.start(range(100))
cloned.start(range(100))
```

### ノード（TaskStage）のクローン

```python
from celestialflow import TaskStage
from celestialflow.utils.util_clone import clone_stage

# 元のノードを作成
stage = TaskStage(
    "Processor",
    process_func,
    stage_mode="thread",
    execution_mode="thread",
    max_workers=4,
)

# ノードをクローン
cloned_stage = clone_stage(stage)

# 元のノードとクローンノードが独立して実行され、互いに影響しない
stage.start(range(10))
cloned_stage.start(range(10, 20))
```

### タスクグラフのクローン

```python
from celestialflow import TaskGraph
from celestialflow.utils.util_clone import clone_graph

# 元のグラフを作成
graph = TaskGraph(schedule_mode="eager")
graph.set_stages(stages=[stage_a, stage_b])

# グラフをクローンしてテストに使用
cloned_graph = clone_graph(graph)

# クローンしたグラフを実行
cloned_graph.start_graph(init_tasks)
```

## 総合例

以下の例は `clone_executor`、`clone_stage`、`clone_graph` を組み合わせて使用する完全なシナリオを示します：

```python
import asyncio
from celestialflow import TaskExecutor, TaskStage, TaskGraph
from celestialflow.utils.util_clone import clone_executor, clone_stage, clone_graph


def square(x: int) -> int:
    return x * x


def add_one(x: int) -> int:
    return x + 1


async def main():
    # 1. clone_executor ----
    executor = TaskExecutor(
        "Square", square, execution_mode="thread", max_workers=4
    )
    cloned_exe = clone_executor(executor)
    print(f"clone_executor: モード={cloned_exe.execution_mode}")

    # 2. clone_stage ----
    stage = TaskStage(
        "AddOne", add_one, stage_mode="serial", execution_mode="serial"
    )
    cloned_stg = clone_stage(stage)
    print(f"clone_stage: 名前={cloned_stg.get_name()}, mode={cloned_stg.get_stage_mode()}")

    # 3. clone_graph ----
    graph = TaskGraph(schedule_mode="eager")
    a = TaskStage("A", square, execution_mode="thread")
    b = TaskStage("B", add_one, execution_mode="thread")
    graph.set_stages([a, b])
    graph.connect([a], [b])

    cloned_grp = clone_graph(graph)
    print(f"clone_graph: スケジュールモード={cloned_grp.schedule_mode}")
    print(f"接続関係一致: {graph.out_edges == cloned_grp.out_edges}")

    # 元のグラフとクローングラフをそれぞれ実行。状態は完全に独立
    await graph.start_graph({a.get_tag(): [1, 2, 3]})
    await cloned_grp.start_graph(
        {list(cloned_grp.stage_runtime_dict.keys())[0]: [10, 20]}
    )


asyncio.run(main())
```

### ベンチマークテストでの使用

```python
from celestialflow.utils.util_benchmark import benchmark_graph

# benchmark_graph は内部で clone_graph を使用
results = benchmark_graph(
    graph,
    init_tasks_dict={stage_a.get_tag(): range(100)},
    stage_modes=["serial", "thread"],
    execution_sync_modes=["serial", "thread"],
    execution_async_modes=["async"],
)
```

## 注意事項

1. **状態の独立性**: クローン後のオブジェクトは元のオブジェクトと完全に独立しています（新しいインスタンスの構築により実現）。変更は相互に影響しません
2. **接続の再構築**: グラフのクローン時にはノード間の接続関係が再構築されます
3. **関数参照**: クローンは関数参照のみをコピーし、関数自体はコピーしません
4. **パフォーマンスオーバーヘッド**: 大規模グラフのクローンにはある程度のオーバーヘッドがありますが、再構築より高速です
