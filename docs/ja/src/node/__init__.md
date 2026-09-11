# node/__init__.py

> 📅 最終更新日: 2026/09/09

## 役割

`celestialflow.node` パッケージはノード層のすべての公共 API を公開します。`core_nodes` モジュールから `TaskExecutor`、`TaskSplitter`、`TaskRouter` を再エクスポートし、タスクグラフに「実行・分割・ルーティング」の 3 種類の直接使用できるパイプラインコンポーネントを提供します。

> 本モジュールの docstring には歴史的名称「CelestialFlow ステージモジュール」が残っていますが、継続して保持できます。

## 公開エクスポートシンボル（`__all__`）

```python
from celestialflow.node import (
    TaskExecutor,  # 汎用タスク実行器
    TaskSplitter,  # 1→N タスク分割器
    TaskRouter,    # 条件ルーター
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
| `TaskExecutor` | `core_nodes` | `BaseTaskNode[T, R]` | 汎用タスク実行器。単一入力を単一結果にマッピング |
| `TaskSplitter` | `core_nodes` | `BaseTaskNode[Iterable[TItem], Iterable[RItem]]` | 分割器。単一タスクを複数のサブタスクに分割（1→N） |
| `TaskRouter` | `core_nodes` | `BaseTaskNode[T, tuple[str, T]]` | ルーター。ユーザー定義の `router` 関数によりタスクを異なる下流へ振り分け |

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

# 文字列を単一文字に分割
splitter = TaskSplitter("CharSplitter")

# 下流の TaskGraph と組み合わせる:
# graph.connect([splitter], [downstream])
# splitter.run([["abc", "de"]])
```

### TaskRouter — 条件に応じて異なる下流へルーティング

```python
from celestialflow.node import TaskRouter


def by_length(text: str) -> str:
    return "LongPath" if len(text) > 5 else "ShortPath"


router = TaskRouter("LengthRouter", router=by_length)
# graph.connect([router], [long_node, short_node])
```

## 他のモジュールとの関連

- **`core_node`**: 基底クラス `BaseTaskNode` と内部スケジューラ `TaskDispatch` を定義し、すべてのノードのランタイム骨格。
- **`core_nodes`**: 3 つの公共ノードクラスを提供。
- **`runtime`**: ノードは `TaskEnvelope` / `TaskInQueue` / `TaskOutQueue` / `TaskMetrics` を通じてキューとメトリクスを通信。
- **`observability`**: `BaseObserver` を通じて実行進捗をレポート。
- **`persistence`**: `LifecycleInlet` / `LogInlet` を通じてタスクのライフサイクルとログを永続化。

## 注意事項

1. **基底クラスは公共 API ではない**：`BaseTaskNode` と `TaskDispatch` は `__all__` に含まれません。ノード動作をカスタマイズする場合は `TaskExecutor` を継承し `process_task_success` / `get_binding_counter` をオーバーライドしてください。
2. **エントリ層の一貫性**：`celestialflow` トップレベルパッケージエントリ（`docs/zh-CN/src/__init__.md`）からも上記の 3 つのシンボルを直接 `import` できます。
3. **ライフサイクル**：すべてのノードの `start()` / `start_async()` はワンタイム呼び出しです。実行完了後はインスタンスをリセットせず再利用するのではなく、新しいインスタンスを作成してください。
