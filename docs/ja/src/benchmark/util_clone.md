# Clone

> 📅 最終更新日: 2026/08/26

`benchmark/util_clone.py` は実行器、ノード、タスクグラフのクローン機能を提供し、パフォーマンステストと設定再利用に使用します。

## 設計目的

パフォーマンステストでは、同じタスクグラフ設定を複数回実行する必要がありますが、各実行で内部状態が変更されます。クローン機能は完全に独立したコピーを作成し、状態汚染を防止します。

## 主要関数

### clone_executor

`TaskExecutor` インスタンスをクローンします。

```python
def clone_executor[T, R](
    executor: TaskExecutor[T, R],
) -> TaskExecutor[T, R]:
    """
    実行器をクローンします。

    :param executor: クローン対象の実行器
    :return: クローンされた実行器
    """
```

コピーされる属性:
- `name`: 実行器名
- `func`: タスク関数
- `execution_mode`: 実行モード
- `max_workers`: 並行数の上限
- `max_retries`: 最大リトライ回数
- `max_info`: ログ情報の最大長
- `enable_duplicate_check`: 重複チェックスイッチ
- `retry_exceptions`: リトライ可能例外のリスト（`set_retry_exceptions()` で設定）

### clone_stage

`TaskStage` ノードをクローンします。

```python
def clone_stage[T, R](
    stage: TaskStage[T, R],
) -> TaskStage[T, R]:
    """
    ノードをクローンします。

    :param stage: クローン対象のノード
    :return: クローンされたノード
    """
```

クローン手順:
1. executor スタイルのパラメータ集合（`name` / `func` / `execution_mode` / `max_workers` / `max_retries` / `max_info` / `enable_duplicate_check`）を再利用
2. `inspect.signature` でノードクラスの `__init__` のパラメータ集合を調べ、両者の交差のみを保持し、ノードクラスが受け付けないパラメータの引き渡しを回避
3. フィルタリング後のパラメータで元のノードと**同じ型**の新しいインスタンスを構築
4. `retry_exceptions` をコピー

パラメータフィルタリングの影響:
- 通常の `TaskStage` の `__init__` は `(name, func, **kwargs)` であり、フィルタリング後は `name` と `func` のみが保持されます。`execution_mode` などの実行時設定はコピーされず、クローン結果はデフォルト設定を使用します
- `TaskSplitter` の `__init__` は `name` / `split_item` のみを受け取るため、クローン時には `name` のみが渡され、分割ロジックはクラス自身のデフォルト実装が提供します
- `TaskRouter` の `__init__` は必須パラメータ `router` を要求しますが、これはフィルタリング対象に含まれないため、`TaskRouter` を直接クローンすると `TypeError` が発生します

### clone_graph

`TaskGraph` インスタンスをクローンします。

```python
def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    タスクグラフをクローンします。

    :param graph: クローン対象のタスクグラフ
    :return: 新しいタスクグラフインスタンス
    """
```

クローンフロー:
1. ソースノードから BFS（幅優先）で元のグラフを走査し（`graph.order_graph.out_edges` の出辺順序に従う）、全ノードを収集
2. 各ノードをクローンし、元のノード名 → クローンノードのマッピングを確立
3. `set_stages()` ですべてのクローンノードを登録し、`connect()` でノード間の接続関係を再構築
4. グラフ設定をコピー（`name`, `graph_mode`）
5. CelestialTree（`clone_event_client`）と Reporter 設定をコピー（`NullTaskReporter` / `TaskReporter` はクローン可能で、その他の型は `ConfigurationError` を送出します）

## 使用例

### 実行器のクローン

```python
from celestialflow import TaskExecutor
from celestialflow.benchmark.util_clone import clone_executor


def process(x: int) -> int:
    return x * 2


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

# 2 つの実行器は独立して動作
executor.run(range(100))
cloned.run(range(100))
```

### ノード（TaskStage）のクローン

```python
from celestialflow import TaskStage
from celestialflow.benchmark.util_clone import clone_stage


def process_func(x: int) -> int:
    return x + 1


# 元のノードを作成
stage = TaskStage(
    "Processor",
    process_func,
    execution_mode="thread",
    max_workers=4,
)

# ノードをクローン
cloned_stage = clone_stage(stage)

# 元のノードとクローンノードは独立して動作し、相互に影響しない
stage.run(range(10))
cloned_stage.run(range(10, 20))
```

### タスクグラフのクローン

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.benchmark.util_clone import clone_graph


def process_a(x: int) -> int:
    return x * 2


def process_b(x: int) -> int:
    return x + 1


# 元のグラフを作成
graph = TaskGraph(name="CloneDemo", graph_mode="thread")
stage_a = TaskStage("A", process_a)
stage_b = TaskStage("B", process_b)
graph.set_stages(stages=[stage_a, stage_b])
graph.connect([stage_a], [stage_b])

# テスト用にグラフをクローン
cloned_graph = clone_graph(graph)

# クローングラフを実行
init_tasks = {stage_a.get_name(): [1, 2, 3]}
cloned_graph.run(init_tasks)
```

## 総合例

以下の例は `clone_executor`、`clone_stage`、`clone_graph` を組み合わせて使用する完全なシナリオを示します:

```python
import asyncio
from celestialflow import TaskExecutor, TaskStage, TaskGraph
from celestialflow.benchmark.util_clone import clone_executor, clone_stage, clone_graph


def square(x: int) -> int:
    return x * x


def add_one(x: int) -> int:
    return x + 1


async def main():
    # 1. clone_executor ----
    executor = TaskExecutor("Square", square, execution_mode="thread", max_workers=4)
    cloned_exe = clone_executor(executor)
    print(f"clone_executor: モード={cloned_exe.execution_mode}")

    # 2. clone_stage ----
    stage = TaskStage("AddOne", add_one, execution_mode="serial")
    cloned_stg = clone_stage(stage)
    print(
        f"clone_stage: 名前={cloned_stg.get_name()}, モード={cloned_stg.execution_mode}"
    )

    # 3. clone_graph ----
    graph = TaskGraph(name="CloneDemo", graph_mode="thread")
    a = TaskStage("A", square, execution_mode="thread")
    b = TaskStage("B", add_one, execution_mode="thread")
    graph.set_stages([a, b])
    graph.connect([a], [b])

    cloned_grp = clone_graph(graph)
    print(f"clone_graph: グラフモード={cloned_grp.graph_mode}")
    print(
        f"接続関係が一致: {graph.order_graph.out_edges == cloned_grp.order_graph.out_edges}"
    )

    # 元のグラフとクローングラフをそれぞれ実行し、状態は完全に独立
    graph.run({a.get_name(): [1, 2, 3]})
    cloned_grp.run({list(cloned_grp.stage_dict.keys())[0]: [10, 20]})


asyncio.run(main())
```

### ベンチマークテストでの使用

```python
import asyncio
from celestialflow import TaskGraph, TaskStage
from celestialflow.benchmark.util_benchmark import benchmark_graph


def task(x: int) -> int:
    return x * 2


async def async_task(x: int) -> int:
    return x * 2


async def main():
    stage_a = TaskStage("A", task)
    stage_b = TaskStage("B", task)
    async_stage_a = TaskStage("A", async_task)
    async_stage_b = TaskStage("B", async_task)

    sync_graph = TaskGraph(name="BenchSync")
    sync_graph.set_stages(stages=[stage_a, stage_b])
    async_graph = TaskGraph(name="BenchAsync")
    async_graph.set_stages(stages=[async_stage_a, async_stage_b])

    # benchmark_graph は内部で clone_graph を使用し、結果辞書を返す
    results = await benchmark_graph(
        sync_graph=sync_graph,
        async_graph=async_graph,
        init_tasks_dict={stage_a.get_name(): range(100)},
        graph_modes=["serial", "thread", "async"],
        execution_modes=["serial", "thread", "async"],
    )
    print(results["table"])


asyncio.run(main())
```

## 注意事項

1. **状態の独立性**: クローン後のオブジェクトは元のオブジェクトと完全に独立しています（新しいインスタンスを構築することで実現）。変更は相互に影響しません
2. **接続の再構築**: グラフのクローン時にはノード間の接続関係が再構築されます
3. **関数参照**: クローンは関数参照のみをコピーし、関数自体はコピーしません
4. **パフォーマンスオーバーヘッド**: 大規模グラフのクローンにはある程度のオーバーヘッドがありますが、再構築より高速です
5. **設定のフォールバック**: `clone_stage` はノードクラスの `__init__` が受け入れるパラメータのみをコピーするため、通常の `TaskStage` では実行モードなどの実行時設定がデフォルト値にフォールバックします; `TaskRouter` は必須パラメータ `router` が欠落しているためクローンできません
