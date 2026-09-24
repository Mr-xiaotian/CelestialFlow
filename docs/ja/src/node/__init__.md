# src/celestialflow/node/__init__.py

> 📅 最終更新日: 2026/09/24

## 役割

`celestialflow.node` パッケージはノード層のすべての公共 API を公開します。`core_nodes` モジュールから `TaskExecutor`、`TaskSplitter`、`TaskRouter` を再エクスポートし、タスクグラフに「実行・分割・ルーティング」の 3 種類の、そのままグラフノードとして使用できるパイプラインコンポーネントを提供します。

## 公開エクスポートシンボル（`__all__`）

```python
from celestialflow.node import (
    TaskExecutor,  # 通用任务执行器
    TaskSplitter,  # 1→N 任务拆分器
    TaskRouter,  # 条件路由器
)
```

完全な `__all__`:

```python
__all__ = [
    "TaskExecutor",
    "TaskRouter",
    "TaskSplitter",
]
```

> ⚠️ `BaseTaskNode` と `TaskDispatch` は `__all__` に **含まれず**、`TaskExecutor` / `TaskSplitter` / `TaskRouter` が構築時に内部的に使用する内部抽象です。外部コードが直接依存してはなりません。

## 3 つのコアノードクラス

| エクスポートシンボル | ソースモジュール | 親クラス | 用途 |
|---------|-------|------|------|
| `TaskExecutor` | `core_nodes` | `BaseTaskNode[T, R, R]` | 汎用タスク実行器。単一入力を単一結果にマッピング |
| `TaskSplitter` | `core_nodes` | `BaseTaskNode[T, Iterable[RItem], RItem]` | 分割器。単一タスクを複数のサブタスクに分割（1→N） |
| `TaskRouter` | `core_nodes` | `BaseTaskNode[T, dict[str, Y], Y]` | ルーター。`func` が `{下流名: ペイロード}` マッピングを返し、それに基づいて振り分け |

> 3 つのノードクラスはいずれも独自の `__init__` を定義せず、`BaseTaskNode.__init__(name, func, *, execution_mode="serial", max_workers=None, max_retries=1, max_queue_size=0, max_info=50)` をそのまま再利用します；`func` は必須です。

## 使用例

### TaskExecutor — 独立したタスク群の実行

```python
from celestialflow.node import TaskExecutor


def double(x: int) -> int:
    return x * 2


executor = TaskExecutor("Doubler", func=double, execution_mode="serial")
executor.run([1, 2, 3, 4, 5])

for task, result in executor.get_success_pairs():
    print(f"{task} -> {result}")
```

### TaskSplitter — 1 つの集合を複数のサブタスクに分割

```python
from celestialflow.node import TaskSplitter


def split_chars(text: str) -> list[str]:
    return list(text)


splitter = TaskSplitter("CharSplitter", split_chars)

# 配合下游 TaskGraph:
# graph.connect([splitter], [downstream])
# splitter.run(["abc"])
```

### TaskRouter — 条件に応じて異なる下流へルーティング

```python
from celestialflow.node import TaskRouter


def route_by_length(text: str) -> dict[str, str]:
    target = "LongPath" if len(text) > 5 else "ShortPath"
    return {target: text}


router = TaskRouter("LengthRouter", route_by_length)
# graph.connect([router], [long_node, short_node])
```

## 他のモジュールとの関連

- **`core_node`**: 基底クラス `BaseTaskNode` と内部スケジューラ `TaskDispatch` を定義し、すべてのノードのランタイム骨格です。
- **`core_nodes`**: 3 つの公共ノードクラスを提供します。
- **`runtime`**: ノードは `TaskEnvelope` / `TaskInQueue` / `TaskOutQueue` / `TaskMetrics` を通じてキューとメトリクスを通信します。
- **`observability`**: `BaseObserver` を通じて実行進捗をレポートします。
- **`persistence`**: `LifecycleInlet` / `LogInlet` を通じてタスクのライフサイクルとログを永続化します。

## 注意事項

1. **基底クラスは公共 API ではない**：`BaseTaskNode` と `TaskDispatch` は `__all__` に含まれません。ノード動作をカスタマイズする場合は `TaskExecutor` を継承し `process_task_success` をオーバーライドしてください。
2. **エントリ層の一貫性**：`celestialflow` トップレベルパッケージエントリ（`docs/zh-CN/src/__init__.md`）からも上記の 3 つのシンボルを直接 `import` できます。
3. **ライフサイクル**：すべてのノードの `start()` / `start_async()` はワンタイム呼び出しです。実行完了後はインスタンスをリセットせず再利用するのではなく、新しいインスタンスを作成してください。
