# benchmark/util_clone.py

> 📅 最終更新日: 2026/09/09

`benchmark/util_clone.py` は実行器とタスクグラフのクローン機能を提供し、パフォーマンステストと設定再利用に使用します。

> ⚠️ 本ファイルはベンチマーク内部のツール関数を定義するもので、**公共 API ではありません**。`clone_executor` / `clone_graph` は `celestialflow` トップレベルパッケージのエントリからエクスポートされません；必要な場合は `from celestialflow.benchmark.util_clone import ...` を通じて直接アクセスしてください。

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

### clone_graph

`TaskGraph` インスタンスをクローンします。

```python
def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    タスクグラフをクローンします。

    本ツールはベンチマークシナリオ専用であるため、``TaskExecutor`` のみで構成された
    タスクグラフのみをサポートし、すべてのノードを :func:`clone_executor` で直接クローンします。

    :param graph: クローン対象のタスクグラフ
    :return: クローンされたタスクグラフ
    :raises ConfigurationError: ``TaskExecutor`` 以外のノードが含まれる場合に送出
    """
```

クローンフロー:
1. ソースノードから BFS（幅優先）で元のグラフを走査し（`graph.order_graph.out_edges` の出辺順序に従う）、全ノードを収集
2. 各ノードが `TaskExecutor` であることをアサート；`TaskSplitter` / `TaskRouter` などの特化ノードに遭遇した場合は即座に `ConfigurationError` を送出します
3. 各ノードをクローンし、元のノード名 → クローンノードのマッピングを確立
4. `set_nodes()` ですべてのクローンノードを登録し、`connect()` でノード間の接続関係を再構築
5. グラフ設定をコピー（`name`, `graph_mode`）
6. CelestialTree（`clone_event_client`）と Reporter 設定をコピー（`NullTaskReporter` / `TaskReporter` はクローン可能で、その他の型は `ConfigurationError` を送出します）

> ⚠️ **`clone_graph` は全ノード型の保持を保証しません**：`TaskExecutor` ノードのみが同じ型としてクローンされます；`TaskSplitter` / `TaskRouter` などの特化ノードは同じサブクラスとしてクローンされず、その分割 / ルーティング動作も保持されません。本ツールはベンチマーク内部ツールであり、「`TaskExecutor` のみで構成され、ベンチマークテストに使用される」タスクグラフにのみ適用されます。

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

### タスクグラフのクローン

```python
from celestialflow import TaskGraph, TaskExecutor
from celestialflow.benchmark.util_clone import clone_graph


def process_a(x: int) -> int:
    return x * 2


def process_b(x: int) -> int:
    return x + 1


# 元のグラフを作成
graph = TaskGraph(name="CloneDemo", graph_mode="thread")
node_a = TaskExecutor("A", process_a)
node_b = TaskExecutor("B", process_b)
graph.set_nodes(nodes=[node_a, node_b])
graph.connect([node_a], [node_b])

# テスト用にグラフをクローン
cloned_graph = clone_graph(graph)

# クローングラフを実行
init_tasks = {node_a.get_name(): [1, 2, 3]}
cloned_graph.run(init_tasks)
```

## 総合例

以下の例は `clone_executor` と `clone_graph` を組み合わせて使用する完全なシナリオを示します:

```python
import asyncio
from celestialflow import TaskExecutor, TaskGraph
from celestialflow.benchmark.util_clone import clone_executor, clone_graph


def square(x: int) -> int:
    return x * x


def add_one(x: int) -> int:
    return x + 1


async def main():
    # 1. clone_executor ----
    executor = TaskExecutor("Square", square, execution_mode="thread", max_workers=4)
    cloned_exe = clone_executor(executor)
    print(f"clone_executor: モード={cloned_exe.execution_mode}")

    # 2. clone_graph ----
    graph = TaskGraph(name="CloneDemo", graph_mode="thread")
    a = TaskExecutor("A", square, execution_mode="thread")
    b = TaskExecutor("B", add_one, execution_mode="thread")
    graph.set_nodes([a, b])
    graph.connect([a], [b])

    cloned_grp = clone_graph(graph)
    print(f"clone_graph: グラフモード={cloned_grp.graph_mode}")
    print(
        f"接続関係が一致: {graph.order_graph.out_edges == cloned_grp.order_graph.out_edges}"
    )

    # 元のグラフとクローングラフをそれぞれ実行し、状態は完全に独立
    graph.run({a.get_name(): [1, 2, 3]})
    cloned_grp.run({list(cloned_grp.node_dict.keys())[0]: [10, 20]})


asyncio.run(main())
```

### ベンチマークテストでの使用

```python
import asyncio
from celestialflow import TaskGraph, TaskExecutor
from celestialflow.benchmark.util_benchmark import benchmark_graph


def task(x: int) -> int:
    return x * 2


async def async_task(x: int) -> int:
    return x * 2


async def main():
    node_a = TaskExecutor("A", task)
    node_b = TaskExecutor("B", task)
    async_node_a = TaskExecutor("A", async_task)
    async_node_b = TaskExecutor("B", async_task)

    sync_graph = TaskGraph(name="BenchSync")
    sync_graph.set_nodes(nodes=[node_a, node_b])
    async_graph = TaskGraph(name="BenchAsync")
    async_graph.set_nodes(nodes=[async_node_a, async_node_b])

    # benchmark_graph は内部で clone_graph を使用し、結果辞書を返す
    results = await benchmark_graph(
        sync_graph=sync_graph,
        async_graph=async_graph,
        init_tasks_dict={node_a.get_name(): range(100)},
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
5. **内部ツール**: `clone_executor` / `clone_graph` はベンチマークの内部ツールであり、トップレベルパッケージエントリの `__all__` に含まれません。シグネチャ/セマンティクスはベンチマーク内部実装の調整に伴い変更される可能性があります
6. **ノード型制限**: `clone_graph` は `TaskExecutor` ノードのみサポート；`TaskSplitter` / `TaskRouter` などの特化ノードに遭遇した場合は `ConfigurationError` を送出し、これらのサブクラスの型と動作は保持されません
