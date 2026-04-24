# TaskGraph

> 📅 最終更新日: 2026/04/24

`TaskGraph` は CelestialFlow のコアスケジューラーであり、一連の `TaskStage` ノードの依存関係、実行フロー、リソース割り当て、およびライフサイクルを管理します。

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

### パラメータ説明

- **schedule_mode**: スケジューリングモード。
  - `eager` (デフォルト): すべてのノードを一括で起動し、依存関係はデータフローで自動制御されます。並列度の最大化に適しています。
  - `staged`: レイヤー別実行。DAG のみに適用されます。レイヤー順に逐次起動し、前のレイヤーがすべて完了してから次のレイヤーを起動します。
- **log_level**: グローバルログレベル（TRACE/DEBUG/SUCCESS/INFO/WARNING/ERROR/CRITICAL）。

### ノードの設定

```python
def set_stages(self, root_stages: list[TaskStage], stages: list[TaskStage]):
    """
    タスクグラフのノードを設定します。
    
    :param root_stages: エントリノードリスト（ルートノード）。複数ルートノード（フォレスト構造）をサポートします。
    :param stages: その他の非ルートノードリスト（オプション）。
    """
```

## コア機能

### グラフ構築と分析

- **自動構築**: `root_stages` とノード間の接続関係 (`out_edges`) に基づいて、グラフ構造全体を自動的に走査して構築します。
- **DAG 検出**: 有向非巡回グラフ (DAG) であるかどうかを自動検出します。
- **レイヤー分析**: DAG の場合、`staged` スケジューリングや可視化表示のためにノードのレイヤーを自動計算します。

### 実行の開始

```python
def start_graph(self, init_tasks_dict: dict, put_termination_signal: bool = True):
    """
    タスクグラフを起動します。
    
    :param init_tasks_dict: 初期タスクデータ、フォーマットは {stage_tag: [task_data, ...]}
    :param put_termination_signal: 初期タスクの後に終了シグナルを自動注入するかどうか。
    """
```

例：
```python
graph = TaskGraph(schedule_mode="eager")
graph.set_stages(root_stages=[stage_a, stage_b], stages=[])
graph.start_graph({
    stage_a.get_tag(): [1, 2, 3, 4, 5]
})
```

### リソース管理

- **プロセス管理**: 子プロセスの自動作成と管理（`process` モードの Stage 用）。
- **キュー管理**: ノード間の通信キュー (`TaskInQueue`, `TaskOutQueue`) を自動作成。
- **グレースフル終了**: タスク完了後にすべての子プロセスが正しく終了すること、または異常時に強制終了されることを保証。

### 監視とレポート

- **ランタイムスナップショット**: `collect_runtime_snapshot()` で各ノードの実行状態（処理数、バックログ数、レートなど）を収集。
- **エラー永続化**: ランタイムのエラーログをローカル JSONL ファイル (`fallback/` ディレクトリ) に永続化。
- **Web 報告**: `TaskReporter` を統合し、状態をリアルタイムで Web UI にプッシュ。

## 設定メソッド

### set_reporter

```python
def set_reporter(self, is_report=False, host="127.0.0.1", port=5000):
    """
    レポーターを設定します。Web UI への状態プッシュに使用します。

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
    CelestialTree クライアントを設定します。イベントトレースに使用します。

    :param use_ctree: CelestialTree を使用するかどうか
    :param host: サービスのホストアドレス
    :param http_port: HTTP ポート
    :param grpc_port: gRPC ポート
    :param transport: 転送プロトコル
    """
```

### set_graph_mode

```python
def set_graph_mode(self, stage_mode: str, execution_mode: str):
    """
    すべてのノードの実行モードを一括設定します。

    :param stage_mode: ノードの実行モード ('serial'、'thread'、または 'process')
    :param execution_mode: ノード内部の実行モード ('serial'、'thread'、または 'async')
    """
```

### _set_log_level

```python
def _set_log_level(self, level="SUCCESS"):
    """
    グローバルログレベルを設定します。
    """
```

## データクエリメソッド

### 状態クエリ

```python
# ノード状態辞書を取得
def get_status_dict(self) -> dict[str, dict]:
    """各ノードのリアルタイム状態を返します。"""

# グラフサマリーを取得
def get_graph_summary(self) -> dict:
    """グローバル統計（成功数、失敗数、バックログ数など）を返します。"""
```

### 分析クエリ

```python
# 分析情報を取得
def get_graph_analysis(self) -> dict:
    """isDAG, schedule_mode, class_name, layers_dict などの情報を返します。"""

# 構造 JSON を取得
def get_structure_json(self) -> list[dict]:
    """グラフ構造の JSON 表現を返します。"""

# 構造リストを取得
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
# ステージ別に失敗タスクを取得
def get_fail_by_stage_dict(self):
    """{stage_tag: [failed_tasks]} 形式の辞書を返します。"""

# エラータイプ別に失敗タスクを取得
def get_fail_by_error_dict(self):
    """{error_type: [failed_tasks]} 形式の辞書を返します。"""

# fallback ファイルパスを取得
def get_fallback_path(self) -> str:
    """エラーログファイルのパスを返します。"""
```

### トレースクエリ

```python
# 入力トレースを取得
def get_stage_input_trace(self, stage_tag: str) -> str:
    """指定ノードの入力イベントトレースを取得します（ctree の有効化が必要）。"""

# エラートレースを取得
def get_error_trace(self, error_id: int):
    """指定エラーのトレース情報を取得します。"""
```

## タスク注入

### put_stage_queue

```python
def put_stage_queue(self, tasks_dict: dict, put_termination_signal=True):
    """
    ノードキューにタスクを動的に注入します。

    :param tasks_dict: {stage_tag: [tasks]}
    :param put_termination_signal: 終了シグナルを注入するかどうか
    """
```

例：
```python
# タスクを動的に注入
graph.put_stage_queue({
    stage_a.get_tag(): [6, 7, 8]
})

# 終了シグナルを注入
from celestialflow import TerminationSignal
graph.put_stage_queue({
    stage_a.get_tag(): [TerminationSignal()]
})
```

## スケジューリングモード詳解

### Eager モード

- すべてのノードを即座に起動
- 依存関係はキューフローで自動制御
- 並列度を最大化
- 大半のシナリオに適用

### Staged モード

- レイヤー順に逐次実行
- 前のレイヤーがすべて完了してから次のレイヤーを起動
- DAG のみに適用
- デバッグ、パフォーマンス分析、リソース制御に適用

## 注意事項

1. **非 DAG グラフ**: 有環グラフでは、終了シグナルの自動注入は推奨されません。Web インターフェースで手動制御してください。
2. **プロセスクリーンアップ**: 異常時にはフレームワークが子プロセスを強制終了し、ログを記録します。
3. **未消費タスク**: 停止時に未消費のタスクを収集し、エラーとして記録します。
4. **Web 監視**: Web サービスを先に起動してから、`set_reporter(True)` を設定する必要があります。

## 例

```python
from celestialflow import TaskStage, TaskGraph

# ノードを作成
stage_a = TaskStage("A", func=process_a, execution_mode="thread", stage_mode="process")
stage_b = TaskStage("B", func=process_b, execution_mode="serial", stage_mode="process")
stage_c = TaskStage("C", func=process_c, execution_mode="serial", stage_mode="process")

# グラフを構築
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
