# ReporterTaskGraph

> 📅 最終更新日: 2026/08/31

`observability/util_types.py` は、`TaskReporter` が依存するタスクグラフプロトコルインターフェース `ReporterTaskGraph` とタスクステージプロトコルインターフェース `ReporterTaskStage` を定義します。これらは `Protocol` クラスであり、`TaskReporter` が具体的な `TaskGraph` / `TaskStage` 型をインポートせずに依存関係を宣言できるようにします。

## コア型

### ReporterTaskGraph

`TaskReporter` が依存する最小限のタスクグラフインターフェースプロトコル。

```python
class ReporterTaskGraph(Protocol):
    """TaskReporter 依赖的最小任务图接口。"""

    @property
    def stage_dict(self) -> Mapping[str, ReporterTaskStage]:
        """名前でインデックスされる読み取り専用ノードマッピングを返す。"""
        ...

    def get_graph_id(self) -> str: ...

    def get_stages_summary(self) -> dict[str, dict[str, Any]]: ...

    def get_edges(self) -> dict[str, list[str]]: ...

    def get_source_names(self) -> list[str]: ...

    def get_lifecycle_path(self) -> Path: ...

    def get_graph_analysis(self) -> dict[str, Any]: ...

    def collect_runtime_snapshot(self) -> tuple[dict[str, Any], float]: ...
```

| メソッド | 戻り値 | 説明 |
|------|--------|------|
| `stage_dict` | `Mapping[str, ReporterTaskStage]` | 名前でインデックスされる読み取り専用ノードマッピングを返す（property） |
| `get_graph_id()` | `str` | 現在のタスクグラフの一意な識別子を取得 |
| `get_stages_summary()` | `dict[str, dict[str, Any]]` | 全 stage のサマリを返す（`name`、`func_name`、`execution_mode`、`max_workers` など） |
| `get_edges()` | `dict[str, list[str]]` | グラフ構造内の辺集合を返す（`{from_name: [to_name, ...]}`） |
| `get_source_names()` | `list[str]` | 上流入力のないソース stage 名のリストを返す |
| `get_lifecycle_path()` | `Path` | ライフサイクル永続化ファイルのパスを取得 |
| `get_graph_analysis()` | `dict[str, Any]` | グラフ分析データを取得（トポロジ情報など） |
| `collect_runtime_snapshot()` | `tuple[dict[str, Any], float]` | 最新のランタイムスナップショットを収集（stage 別に集計された状態辞書 + 収集タイムスタンプ） |

### ReporterTaskStage

`TaskReporter` が依存する最小限のタスクステージインターフェースプロトコル（図が `stage_dict` を通じてステージを公開する場合のみ使用）。

```python
class ReporterTaskStage(Protocol):
    """TaskReporter 依赖的最小任务阶段接口。"""

    def put_task(self, task: Any) -> None: ...

    def put_signal(self) -> None: ...
```

| メソッド | 戻り値 | 説明 |
|------|--------|------|
| `put_task(task)` | `None` | 単一のタスクをステージの入力キューに注入（動的タスク注入用） |
| `put_signal()` | `None` | ステージの入力キューに終了シグナルを入れる |

## 使用例

### TaskReporter での型アノテーション

```python
from celestialflow.observability.util_types import (
    ReporterTaskGraph,
    ReporterTaskStage,
)


# TaskReporter 使用 Protocol 定义依赖，避免循环引用
class TaskReporter:
    def __init__(
        self,
        host: str,
        port: int,
        task_graph: ReporterTaskGraph,  # 接受任何满足该协议的实例
    ) -> None: ...


# 满足 ReporterTaskStage 协议的最小实现示例
class MinimalStage:
    def put_task(self, task): ...

    def put_signal(self): ...
```

## 注意事項

- `ReporterTaskGraph` と `ReporterTaskStage` はどちらも `typing.Protocol` であり、構造的型付け（structural subtyping）に属します。対応するメソッドを実装した任意のクラスは、型チェッカーによってプロトコルを満たすと見なされます。
- Protocol 設計により、`TaskReporter` と `TaskGraph` / `TaskStage` の間の循環依存を回避しています。
- このファイルは `core_report.py` からインポートされて使用されます。
