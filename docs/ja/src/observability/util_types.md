# ReporterTaskGraph

> 📅 最終更新日: 2026/06/18

`observability/util_types.py` は、`TaskReporter` が依存するタスクグラフプロトコルインターフェース `ReporterTaskGraph` を定義します。これは `Protocol` クラスであり、`TaskReporter` が具体的な `TaskGraph` 型をインポートせずに依存関係を宣言できるようにします。

## コア型

### ReporterTaskGraph

`TaskReporter` が依存する最小限のタスクグラフインターフェースプロトコルです。

```python
class ReporterTaskGraph(Protocol):
    """TaskReporter 依赖的最小任务图接口。"""

    def collect_runtime_snapshot(self) -> None: ...

    def get_graph_id(self) -> str: ...

    def put_stage_queue(
        self,
        tasks_dict: Mapping[str, Iterable[Any]],
        put_termination_signal: bool = True,
    ) -> None: ...

    def get_fallback_path(self) -> Path: ...

    def get_status_snapshot(self) -> dict[str, Any]: ...

    def get_structure_graph(self) -> dict[str, Any]: ...

    def get_graph_analysis(self) -> dict[str, Any]: ...
```

| メソッド | 戻り値 | 説明 |
|------|--------|------|
| `collect_runtime_snapshot()` | `None` | 最新のランタイムスナップショットを収集 |
| `get_graph_id()` | `str` | 現在のタスクグラフの一意な識別子を取得 |
| `put_stage_queue(tasks_dict, put_termination_signal)` | `None` | 注入タスクを指定 stage のキューに入れる |
| `get_fallback_path()` | `Path` | fallback 永続化ファイルのパスを取得 |
| `get_status_snapshot()` | `dict[str, Any]` | 実行状態スナップショットを取得（各 stage のカウント等） |
| `get_structure_graph()` | `dict[str, Any]` | グラフ構造情報を取得（ノードとエッジ） |
| `get_graph_analysis()` | `dict[str, Any]` | グラフ分析データを取得（トポロジ情報等） |

## 使用例

### TaskReporter での型アノテーション

```python
from celestialflow.observability.util_types import ReporterTaskGraph

# TaskReporter 使用 Protocol 定义依赖，避免循环引用
class TaskReporter:
    def __init__(
        self,
        host: str,
        port: int,
        task_graph: ReporterTaskGraph,  # 接受任何满足该协议的实例
        log_inlet: LogInlet,
    ) -> None:
        ...
```

## 注意事項

- `ReporterTaskGraph` は `typing.Protocol` であり、構造的部分型（structural subtyping）に属します。このプロトコルのメソッドを実装した任意のクラスは、型チェッカーによってプロトコルを満たすと見なされます。
- Protocol 設計により、`TaskReporter` と `TaskGraph` の間の循環依存を回避しています。
- このファイルは `core_report.py` からインポートされて使用されます。
