# src/celestialflow/observability/util_types.py

> 📅 最終更新日: 2026/09/24

`observability/util_types.py` は、`TaskReporter` が依存する最小限のタスクグラフプロトコルインターフェース `ReporterTaskGraph` と最小限のノードプロトコルインターフェース `ReporterTaskNode` を定義します。これらは `Protocol` クラスであり、`TaskReporter` が具体的な `TaskGraph` / `BaseTaskNode` 型をインポートせずに依存関係を宣言できるようにします。

## コア型

### ReporterTaskGraph

`TaskReporter` が依存する最小限のタスクグラフインターフェースプロトコル。

```python
class ReporterTaskGraph(Protocol):
    """TaskReporter 依赖的最小任务图接口。"""

    @property
    def node_dict(self) -> Mapping[str, ReporterTaskNode]:
        """名前でインデックスされる読み取り専用ノードマッピングを返す。"""
        ...

    def get_graph_id(self) -> str: ...

    def get_nodes(self) -> list[str]: ...

    def get_node_meta(self) -> dict[str, dict[str, Any]]: ...

    def get_edges(self) -> dict[str, list[str]]: ...

    def get_source_nodes(self) -> list[str]: ...

    def get_lifecycle_path(self) -> Path: ...

    def get_graph_analysis(self) -> dict[str, Any]: ...
```

| メソッド | 戻り値 | 説明 |
|------|--------|------|
| `node_dict` | `Mapping[str, ReporterTaskNode]` | 名前でインデックスされる読み取り専用ノードマッピングを返す（property） |
| `get_graph_id()` | `str` | 現在のタスクグラフの一意な識別子を取得 |
| `get_nodes()` | `list[str]` | すべてのノード名のリストを返す |
| `get_node_meta()` | `dict[str, dict[str, Any]]` | 各ノードの構築期メタ情報（`class_name` / `execution_mode` / `max_workers`）を返す。図元情報とともに一度にレポートされる |
| `get_edges()` | `dict[str, list[str]]` | グラフ構造内の辺集合を返す（`{from_name: [to_name, ...]}`） |
| `get_source_nodes()` | `list[str]` | 上流入力のないソースノード名のリストを返す |
| `get_lifecycle_path()` | `Path` | ライフサイクル永続化ファイルのパスを取得 |
| `get_graph_analysis()` | `dict[str, Any]` | グラフ分析データ（トポロジ情報など）を取得 |

### ReporterTaskNode

`TaskReporter` が依存する最小ノードインターフェースプロトコル。

```python
class ReporterTaskNode(Protocol):
    """TaskReporter 依赖的最小节点接口。"""

    def put_task(self, task: Any) -> None: ...

    def put_signal(self) -> None: ...

    def get_meta(self) -> dict[str, Any]: ...

    def get_snapshot(self) -> dict[str, Any]: ...
```

| メソッド | 戻り値 | 説明 |
|------|--------|------|
| `put_task(task)` | `None` | 単一のタスクをノードの入力キューに注入（動的タスク注入用） |
| `put_signal()` | `None` | ノードの入力キューに終了シグナルを入れる |
| `get_meta()` | `dict[str, Any]` | ノードの構築期メタ情報（`class_name` / `execution_mode` / `max_workers`）を返す |
| `get_snapshot()` | `dict[str, Any]` | ノードのランタイムスナップショット（状態、カウント、経過時間、上流下流カウント）を返す |

## 使用例

### TaskReporter での型アノテーション

```python
from celestialflow.observability.util_types import (
    ReporterTaskGraph,
    ReporterTaskNode,
)


# TaskReporter は Protocol を使って依存を定義し、循環参照を回避
class TaskReporter:
    def __init__(
        self,
        host: str,
        port: int,
        task_graph: ReporterTaskGraph,  # プロトコルを満たす任意のインスタンスを受け入れる
    ) -> None: ...


# ReporterTaskNode プロトコルを満たす最小限の実装例
class MinimalNode:
    def put_task(self, task): ...

    def put_signal(self): ...
```

## 注意事項

- `ReporterTaskGraph` と `ReporterTaskNode` はどちらも `typing.Protocol` であり、構造的型付け（structural subtyping）に属します。対応するメソッドを実装した任意のクラスは、型チェッカーによってプロトコルを満たすと見なされます。
- Protocol 設計により、`TaskReporter` と `TaskGraph` / `BaseTaskNode` の間の循環依存を回避しています。
- このファイルは `core_report.py` からインポートされて使用されます。
