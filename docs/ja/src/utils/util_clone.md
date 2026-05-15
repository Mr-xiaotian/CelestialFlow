# Clone

> 📅 最終更新日: 2026/05/15

`utils/util_clone.py` はエグゼキューター、ノード、タスクグラフのクローン機能を提供し、パフォーマンステストと設定の再利用に使用されます。

## 設計目的

パフォーマンステストでは、同じタスクグラフ設定を複数回実行する必要がありますが、各実行で内部状態が変更されます。クローン機能は完全に独立したコピーを作成し、状態汚染を回避します。

## 主要関数

### clone_executor

`TaskExecutor` インスタンスをクローンします。

```python
def clone_executor(executor: TaskExecutor) -> TaskExecutor:
    """
    エグゼキューターをクローンします。

    :param executor: クローン対象のエグゼキューター
    :return: 新しいエグゼキューターインスタンス
    """
```

コピーされる属性：
- `name`: エグゼキューター名
- `func`: タスク関数
- `execution_mode`: 実行モード
- `max_workers`: 並行数制限
- `max_retries`: 最大リトライ回数
- `max_info`: ログメッセージ最大長
- `unpack_task_args`: 引数展開の有無
- `enable_duplicate_check`: 重複チェックのトグル
- `log_level`: ログレベル
- `retry_exceptions`: リトライ可能な例外リスト

### clone_stage

`TaskStage` インスタンスをクローンします。

```python
def clone_stage(stage: TaskStage) -> TaskStage:
    """
    ノードをクローンします。

    :param stage: クローン対象のノード
    :return: 新しいノードインスタンス
    """
```

`TaskExecutor` の属性に加えて、以下もコピーします：
- `stage_mode`: ノードモード

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

クローンプロセス：
1. 元のグラフのすべてのノードを走査（BFS）
2. 各ノードをクローンしマッピングを構築
3. ノード間の接続関係を再構築
4. グラフ設定をコピー（schedule_mode, log_level）
5. CelestialTree と Reporter の設定をコピー

## 使用例

### エグゼキューターのクローン

```python
from celestialflow import TaskExecutor
from celestialflow.utils.util_clone import clone_executor

# 元のエグゼキューターを作成
executor = TaskExecutor(
    "Processor",
    process,
    execution_mode="thread",
    max_workers=10,
    max_retries=3,
)

# エグゼキューターをクローン
cloned = clone_executor(executor)

# 2つのエグゼキューターが独立して実行
executor.start(range(100))
cloned.start(range(100))
```

### タスクグラフのクローン

```python
from celestialflow import TaskGraph
from celestialflow.utils.util_clone import clone_graph

# 元のグラフを作成
graph = TaskGraph(schedule_mode="eager")
graph.set_stages(stages=[stage_a, stage_b])

# テスト用にグラフをクローン
cloned_graph = clone_graph(graph)

# クローンしたグラフを実行
cloned_graph.start_graph(init_tasks)
```

### ベンチマークでの使用

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

1. **状態の独立性**: クローンされたオブジェクトは元のオブジェクトと完全に独立、変更は相互に影響しない
2. **接続の再構築**: グラフのクローン時にノード間の接続関係を再構築
3. **関数参照**: クローンは関数参照のみコピー、関数自体はコピーしない
4. **パフォーマンスオーバーヘッド**: 大規模グラフのクローンには一定のオーバーヘッドがあるが、再構築より高速
