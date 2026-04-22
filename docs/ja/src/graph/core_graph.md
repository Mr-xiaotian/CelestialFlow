# TaskGraph

> 📅 最終更新日: 2026/04/22

`TaskGraph` は CelestialFlow のコアスケジューラーで、一連の `TaskStage` ノードの依存関係、実行フロー、リソース割り当て、ライフサイクルの管理を担当します。

## 初期化

```python
class TaskGraph:
    def __init__(
        self,
        schedule_mode: str = "eager",
        log_level: str = "SUCCESS",
    ):
        ...
```

### パラメーター説明

- **schedule_mode**: スケジューリングモードです。
  - `eager`（デフォルト）: すべてのノードが一度に起動し、依存関係はデータフローを通じて自動的に制御されます。並列度を最大化するのに適しています。
  - `staged`: レイヤーごとの実行です。DAG にのみ適用されます。トポロジカル順序でレイヤーごとにノードが起動され、前のレイヤーがすべて完了してから次のレイヤーが開始されます。
- **log_level**: グローバルログレベルです（TRACE/DEBUG/SUCCESS/INFO/WARNING/ERROR/CRITICAL）。

### ノードの設定

```python
def set_stages(self, root_stages: list[TaskStage], stages: list[TaskStage] = None):
    """
    タスクグラフのノードを設定します。
    
    :param root_stages: エントリノード（ルートノード）のリストです。複数のルートノード（フォレスト構造）をサポートします。
    :param stages: その他の非ルートノードのリストです（オプション）。
    """
```

## コア機能

### グラフの構築と分析

- **自動構築**: `root_stages` とノード間の接続関係（`out_edges`）に基づいて、自動的にグラフ構造全体をトラバースして構築します。
- **DAG 検出**: 有向非巡回グラフ（DAG）であるかどうかを自動的に検出します。
- **レイヤー分析**: DAG の場合、`staged` スケジューリングや可視化表示のためにノードのレベルを自動的に計算します。

### 実行の開始

```python
def start_graph(self, init_tasks_dict: dict, put_termination_signal: bool = True):
    """
    タスクグラフを開始します。
    
    :param init_tasks_dict: 初期タスクデータです。形式は {stage_tag: [task_data, ...]} です。
    :param put_termination_signal: 初期タスクの後に終了シグナルを自動注入するかどうかです。
    """
```

例：
```python
graph = TaskGraph(schedule_mode="eager")
graph.set_stages(root_stages=[stage_a, stage_b])
graph.start_graph({
    stage_a.get_tag(): [1, 2, 3, 4, 5]
})
```

### リソース管理

- **プロセス管理**: 子プロセスを自動的に作成および管理します（`process` モードの Stage 用）。
- **キュー管理**: ノード間の通信キュー（`TaskInQueue`、`TaskOutQueue`）を自動的に作成します。
- **グレースフル終了**: タスク完了後にすべての子プロセスが正しく終了すること、または例外時に強制終了されることを保証します。

### 監視とレポート

- **ランタイムスナップショット**: `collect_runtime_snapshot()` が各ノードの実行状態（処理数、バックログ数、レートなど）を収集します。
- **エラーの永続化**: ランタイムエラーログをローカル JSONL ファイル（`fallback/` ディレクトリ）に永続化します。
- **Web レポート**: `TaskReporter` を統合し、Web UI にリアルタイムでステータスをプッシュします。

## 設定メソッド

### set_reporter

```python
def set_reporter(self, is_report=False, host="127.0.0.1", port=5000):
    """
    Web UI にステータスをプッシュするためのレポーターを設定します。

    :param is_report: レポーターを有効にするかどうか
    :param host: Web サービスのホストアドレス
    :param port: Web サービスのポート
    """
```

### set_ctree

```python
def set_ctree(
    self,
    use_ctree=False,
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778,
    transport="grpc",
):
    """
    イベント追跡用の CelestialTree クライアントを設定します。

    :param use_ctree: CelestialTree を使用するかどうか
    :param host: サービスのホストアドレス
    :param http_port: HTTP ポート
    :param grpc_port: gRPC ポート
    :param transport: トランスポートプロトコル
    """
```

### set_graph_mode

```python
def set_graph_mode(self, stage_mode: str, execution_mode: str):
    """
    すべてのノードの実行モードを一括設定します。

    :param stage_mode: ノードの実行モード（'serial'、'thread'、または 'process'）
    :param execution_mode: ノードの内部実行モード（'serial' または 'thread'）
    """
```

### set_log_level

```python
def set_log_level(self, level="SUCCESS"):
    """
    グローバルログレベルを設定します。
    """
```

## データクエリメソッド

### ステータスクエリ

```python
# ノードステータス辞書の取得
def get_status_dict(self) -> dict[str, dict]:
    """各ノードのリアルタイムステータスを返します。"""

# グラフサマリーの取得
def get_graph_summary(self) -> dict:
    """グローバル統計（成功数、失敗数、バックログ数など）を返します。"""
```

### 分析クエリ

```python
# 分析情報の取得
def get_graph_analysis(self) -> dict:
    """isDAG、schedule_mode、class_name、layers_dict などの情報を返します。"""

# 構造 JSON の取得
def get_structure_json(self) -> list[dict]:
    """グラフ構造の JSON 表現を返します。"""

# 構造リストの取得
def get_structure_list(self) -> list[str]:
    """フォーマットされた構造リストを返します。"""
```

### NetworkX グラフ

```python
def get_networkx_graph(self):
    """
    タスクグラフの networkx 有向グラフ（DiGraph）を取得します。
    複雑なグラフ分析に使用できます。
    """
```

### エラークエリ

```python
# ステージ別の失敗タスクの取得
def get_fail_by_stage_dict(self):
    """{stage_tag: [failed_tasks]} 形式の辞書を返します。"""

# エラータイプ別の失敗タスクの取得
def get_fail_by_error_dict(self):
    """{error_type: [failed_tasks]} 形式の辞書を返します。"""

# フォールバックファイルパスの取得
def get_fallback_path(self) -> str:
    """エラーログファイルのパスを返します。"""
```

### 追跡クエリ

```python
# 入力追跡の取得
def get_stage_input_trace(self, stage_tag: str) -> str:
    """指定したノードの入力イベント追跡を取得します（ctree の有効化が必要です）。"""

# エラー追跡の取得
def get_error_trace(self, error_id: int):
    """指定したエラーの追跡情報を取得します。"""
```

## タスクの注入

### put_stage_queue

```python
def put_stage_queue(self, tasks_dict: dict, put_termination_signal=True):
    """
    ノードキューに動的にタスクを注入します。

    :param tasks_dict: {stage_tag: [tasks]}
    :param put_termination_signal: 終了シグナルを注入するかどうか
    """
```

例：
```python
# 動的にタスクを注入する
graph.put_stage_queue({
    stage_a.get_tag(): [6, 7, 8]
})

# 終了シグナルを注入する
from celestialflow import TerminationSignal
graph.put_stage_queue({
    stage_a.get_tag(): [TerminationSignal()]
})
```

## スケジューリングモードの詳細

### Eager モード

- すべてのノードが即座に起動します
- 依存関係はキューフローを通じて自動的に制御されます
- 並列度を最大化します
- ほとんどのシナリオに適しています

### Staged モード

- トポロジカル順序でレイヤーごとに実行します
- 前のレイヤーのすべてのノードが完了してから次のレイヤーが開始されます
- DAG にのみ適用されます
- デバッグ、パフォーマンス分析、リソース制御に適しています

## 注意事項

1. **非 DAG グラフ**: 有環グラフの場合、終了シグナルの自動注入は推奨されません。Web UI を使用して手動で制御してください。
2. **プロセスのクリーンアップ**: 例外的な状況では、フレームワークが子プロセスを強制終了してログに記録します。
3. **未消費タスク**: 停止時に未消費のタスクが収集され、エラーとして記録されます。
4. **Web 監視**: まず Web サービスを起動してから、`set_reporter(True)` を設定する必要があります。

## 使用例

```python
from celestialflow import TaskStage, TaskGraph

# ノードの作成
stage_a = TaskStage(func=process_a, execution_mode="thread", stage_mode="process", stage_name="A")
stage_b = TaskStage(func=process_b, execution_mode="serial", stage_mode="process", stage_name="B")
stage_c = TaskStage(func=process_c, execution_mode="serial", stage_mode="process", stage_name="C")

# グラフの構築
graph = TaskGraph(schedule_mode="eager", log_level="INFO")
graph.set_stages(root_stages=[stage_a], stages=[stage_b, stage_c])
graph.connect([stage_a], [stage_b, stage_c])

# 設定
graph.set_reporter(True, host="127.0.0.1", port=5005)

# 起動
graph.start_graph({
    stage_a.get_tag(): range(100)
})
```
