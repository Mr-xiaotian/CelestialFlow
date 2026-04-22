# Clone

`utils/clone.py` は、エグゼキュータ、ステージ、タスクグラフのクローン機能を提供し、パフォーマンステストや設定の再利用に使用されます。

## 設計目的

パフォーマンステストでは、同じタスクグラフ設定を複数回実行する必要がありますが、各実行で内部状態が変更されます。クローン機能により、完全に独立したコピーを作成し、状態汚染を防ぎます。

## 主要関数

### clone_executor

`TaskExecutor` インスタンスをクローンします。

```python
def clone_executor(executor: TaskExecutor) -> TaskExecutor:
    """
    エグゼキュータをクローンします。

    :param executor: クローン対象のエグゼキュータ
    :return: 新しいエグゼキュータインスタンス
    """
```

コピーされる属性:
- `func`: タスク関数
- `execution_mode`: 実行モード
- `max_workers`: 並行数制限
- `max_retries`: 最大リトライ回数
- `max_info`: ログメッセージの最大長
- `unpack_task_args`: 引数を展開するかどうか
- `enable_success_cache`: 成功キャッシュの有効/無効
- `enable_error_cache`: エラーキャッシュの有効/無効
- `enable_duplicate_check`: 重複チェックの有効/無効
- `show_progress`: プログレスバーの有効/無効
- `progress_desc`: プログレスバーの説明
- `log_level`: ログレベル
- `retry_exceptions`: リトライ可能な例外リスト

### clone_stage

`TaskStage` インスタンスをクローンします。

```python
def clone_stage(stage: TaskStage) -> TaskStage:
    """
    ステージをクローンします。

    :param stage: クローン対象のステージ
    :return: 新しいステージインスタンス
    """
```

`TaskExecutor` の属性に加えて、以下もコピーされます:
- `stage_mode`: ステージモード
- `_name`: ステージ名

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

クローン処理:
1. 元のグラフのすべてのステージを走査（BFS）
2. 各ステージをクローンしマッピングを確立
3. ステージ間の接続関係を再構築
4. グラフ設定をコピー（schedule_mode, log_level）
5. CelestialTree と Reporter の設定をコピー

## 使用例

### エグゼキュータのクローン

```python
from celestialflow import TaskExecutor
from celestialflow.utils.clone import clone_executor

# 元のエグゼキュータを作成
executor = TaskExecutor(
    func=process,
    execution_mode="thread",
    max_workers=10,
    max_retries=3,
)

# エグゼキュータをクローン
cloned = clone_executor(executor)
cloned.set_execution_mode("process")  # クローンの設定を変更

# 2つのエグゼキュータが独立して実行
executor.start(range(100))
cloned.start(range(100))
```

### タスクグラフのクローン

```python
from celestialflow import TaskGraph
from celestialflow.utils.clone import clone_graph

# 元のグラフを作成
graph = TaskGraph(schedule_mode="eager")
graph.set_stages(root_stages=[stage_a, stage_b])

# テスト用にグラフをクローン
cloned_graph = clone_graph(graph)
cloned_graph.set_graph_mode("process", "thread")

# クローンしたグラフを実行
cloned_graph.start_graph(init_tasks)
```

### ベンチマークでの使用

```python
from celestialflow.utils.benchmark import benchmark_graph

# 同じグラフ設定を複数回テスト
# benchmark_graph は内部で clone_graph を使用
results = benchmark_graph(
    graph,
    init_tasks_dict={stage_a.get_tag(): range(100)},
    stage_modes=["serial", "process"],
    execution_modes=["serial", "thread"],
)
```

## 注意事項

1. **状態の独立性**: クローンされたオブジェクトは元のオブジェクトと完全に独立しており、変更が互いに影響しません
2. **接続の再構築**: グラフのクローン時にステージ間の接続関係が再構築されます
3. **関数参照**: クローンは関数参照をコピーしますが、関数自体はコピーしません
4. **パフォーマンスオーバーヘッド**: 大規模なグラフのクローンには一定のオーバーヘッドがありますが、再構築よりは高速です
