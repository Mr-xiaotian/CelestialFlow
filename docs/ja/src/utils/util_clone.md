# Clone

> 📅 最終更新日: 2026/05/08

`utils/util_clone.py` はエグゼキューター、ノード、タスクグラフのクローン機能を提供し、パフォーマンステストと設定の再利用に使用します。

## 設計目的

パフォーマンステストでは、同じタスクグラフ設定を複数回実行する必要がありますが、各実行で内部状態が変更されます。クローン機能は完全に独立したコピーを作成し、状態汚染を防ぎます。

## 主要関数

### clone_executor

`TaskExecutor` インスタンスをクローン。

```python
def clone_executor(executor: TaskExecutor) -> TaskExecutor:
```

コピーされる属性：
- `name`: エグゼキューター名
- `func`: タスク関数
- `execution_mode`: 実行モード
- `max_workers`: 並行制限
- `max_retries`: 最大リトライ回数
- `max_info`: ログ情報の最大長
- `unpack_task_args`: 引数展開の有無
- `enable_duplicate_check`: 重複チェックの有無
- `log_level`: ログレベル
- `retry_exceptions`: リトライ可能な例外リスト

### clone_stage

`TaskStage` インスタンスをクローン。

```python
def clone_stage(stage: TaskStage) -> TaskStage:
```

`TaskExecutor` の属性に加えて：
- `stage_mode`: ノードモード

### clone_graph

`TaskGraph` インスタンスをクローン。

```python
def clone_graph(graph: TaskGraph) -> TaskGraph:
```

クローンフロー：
1. 元のグラフの全ノードを走査（BFS）
2. 各ノードをクローンしマッピングを構築
3. ノード間の接続関係を再構築
4. グラフ設定をコピー（schedule_mode, log_level）
5. CelestialTree と Reporter 設定をコピー

## 使用例

### エグゼキューターのクローン

```python
from celestialflow import TaskExecutor
from celestialflow.utils.util_clone import clone_executor

executor = TaskExecutor(
    "Processor",
    process,
    execution_mode="thread",
    max_workers=10,
    max_retries=3,
)

cloned = clone_executor(executor)

executor.start(range(100))
cloned.start(range(100))
```

### タスクグラフのクローン

```python
from celestialflow import TaskGraph
from celestialflow.utils.util_clone import clone_graph

graph = TaskGraph(schedule_mode="eager")
graph.set_stages(stages=[stage_a, stage_b])

cloned_graph = clone_graph(graph)
cloned_graph.start_graph(init_tasks)
```

## 注意事項

1. **状態独立**: クローン後のオブジェクトは元のオブジェクトと完全に独立
2. **接続再構築**: グラフクローン時にノード間の接続関係を再構築
3. **関数参照**: クローンは関数参照のみコピー、関数自体はコピーしない
4. **パフォーマンスオーバーヘッド**: 大規模グラフのクローンには一定のオーバーヘッドがあるが、再構築より高速
