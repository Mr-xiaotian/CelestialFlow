# TaskGraph

> 📅 最終更新日: 2026/05/15

`TaskGraph` は CelestialFlow のコアスケジューラで、一連の `TaskStage` ノードの依存関係、実行フロー、リソース割り当て、ライフサイクルの管理を担当します。

## 初期化

```python
class TaskGraph:
    def __init__(
        self,
        schedule_mode: str = "eager",
        log_level: str = "INFO",
    ):
        ...
```

### パラメータ説明

- **schedule_mode**: スケジューリングモード。
  - `eager`（デフォルト）: すべてのノードを一斉に起動し、依存関係はデータフローにより自動制御。並列度の最大化に適している。
  - `staged`: レイヤーごとに順次実行。DAG のみに適用。レベル順にレイヤーを起動し、前のレイヤーがすべて完了してから次のレイヤーを開始。
- **log_level**: グローバルログレベル（TRACE/DEBUG/INFO/SUCCESS/WARNING/ERROR/CRITICAL）、デフォルトは `"INFO"`。

### ノードの設定

```python
def set_stages(self, stages: list[TaskStage]):
    """
    タスクグラフのノードを設定する。ソースノードは SCC 凝縮により自動計算。
    
    :param stages: すべてのノードのリスト。
    """
```

## コア機能

### グラフの構築と分析

- **自動構築**: ノードリストとノード間の接続関係（`out_edges`）に基づいて、グラフ構造全体を自動的に走査・構築。
- **ソースノードの自動検出**: SCC 凝縮によりソースノード（入次数が 0 のノード）を自動識別。
- **DAG 検出**: 有向非巡回グラフ（DAG）であるかどうかを自動検出。
- **レベル分析**: DAG の場合、`staged` スケジューリングや可視化のためにノードレベルを自動計算。

### 実行の開始

```python
def start_graph(self, init_tasks_dict: dict, put_termination_signal: bool = True):
    """
    タスクグラフを開始する。
    
    :param init_tasks_dict: 初期タスクデータ。形式は {stage_tag: [task_data, ...]}
    :param put_termination_signal: 初期タスク後に終了シグナルを自動注入するかどうか。
    """
```

例：
```python
graph = TaskGraph(schedule_mode="eager")
graph.set_stages(stages=[stage_a, stage_b])
graph.start_graph({
    stage_a.get_tag(): [1, 2, 3, 4, 5]
})
```

### リソース管理

- **キュー管理**: ノード間の通信キュー（`TaskInQueue`、`TaskOutQueue`）を自動作成。
- **グレースフル終了**: タスク完了後、すべてのノードが正しく終了することを保証。

### 監視とレポート

- **ランタイムスナップショット**: `collect_runtime_snapshot()` で各ノードの実行状態（処理数、バックログ数、レートなど）を収集。
- **エラー永続化**: ランタイムのエラーログをローカル JSONL ファイル（`fallback/` ディレクトリ）に永続化。
- **Web レポート**: `TaskReporter` を統合し、Web UI にリアルタイムで状態をプッシュ。

## 設定メソッド

### set_reporter

```python
def set_reporter(self, is_report=False, host="127.0.0.1", port=5000):
    """
    Web UI への状態プッシュ用レポーターを設定。

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
    イベントトレーシング用の CelestialTree クライアントを設定。

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
    すべてのノードの実行モードを一括設定。

    :param stage_mode: ノードの実行モード（'serial' または 'thread'）
    :param execution_mode: ノードの内部実行モード（'serial'、'thread'、または 'async'）
    """
```

### _set_log_level

```python
def _set_log_level(self, level="INFO"):
    """
    グローバルログレベルを設定。
    """
```

## データクエリメソッド

### 状態クエリ

```python
# ノード状態辞書を取得
def get_status_dict(self) -> dict[str, dict]:
    """各ノードのリアルタイム状態を返す。"""

# グラフ概要を取得
def get_graph_summary(self) -> dict:
    """グローバル統計（成功数、失敗数、バックログ数など）を返す。"""
```

### 分析クエリ

```python
# 分析情報を取得
def get_graph_analysis(self) -> dict:
    """isDAG、schedule_mode、class_name、layers_dict などの情報を返す。"""

# 構造 JSON を取得
def get_structure_json(self) -> list[dict]:
    """グラフ構造の JSON 表現を返す。"""

# 構造リストを取得
def get_structure_list(self) -> list[str]:
    """フォーマットされた構造リストを返す。"""
```

### NetworkX グラフ

```python
def get_networkx_graph(self):
    """
    タスクグラフの networkx 有向グラフ（DiGraph）を取得。
    複雑なグラフ分析に使用可能。
    """
```

### エラークエリ

```python
# ステージ別に失敗タスクを取得
def get_fail_by_stage_dict(self):
    """{stage_tag: [failed_tasks]} 形式の辞書を返す。"""

# エラータイプ別に失敗タスクを取得
def get_fail_by_error_dict(self):
    """{error_type: [failed_tasks]} 形式の辞書を返す。"""

# fallback ファイルパスを取得
def get_fallback_path(self) -> str:
    """エラーログファイルのパスを返す。"""
```

### トレースクエリ

```python
# 入力トレースを取得
def get_stage_input_trace(self, stage_tag: str) -> str:
    """指定ノードの入力イベントトレースを取得（ctree の有効化が必要）。"""
```

### その他のクエリ

```python
# 各ノードの履歴状態を取得
def get_stage_history(self) -> dict[str, list[dict]]:
    """各ノードの履歴スナップショットリストを返す。"""

# エラー総数を取得
def get_total_error_num(self) -> int:
    """エラーの総数を返す。"""

# ソースノードリストを取得
def get_source_stages(self) -> list[TaskStage]:
    """ソースノードのリストを返す（SCC 凝縮により自動計算）。"""
```

## タスク注入

### put_stage_queue

```python
def put_stage_queue(self, tasks_dict: dict, put_termination_signal=True):
    """
    ノードキューにタスクを動的に注入。

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

- すべてのノードが即座に開始
- 依存関係はキューフローにより自動制御
- 並列度を最大化
- ほとんどのシナリオに適用

### Staged モード

- レベル順にレイヤーごとに実行
- 前のレイヤーがすべて完了してから次のレイヤーを開始
- DAG のみに適用
- デバッグ、パフォーマンス分析、リソース制御に適用

## 注意事項

1. **非 DAG グラフ**: 循環グラフの場合、終了シグナルの自動注入は推奨されません。代わりに Web インターフェースで手動制御してください。
2. **未消費タスク**: 停止時に未消費のタスクが収集され、エラーとして記録されます。
4. **Web 監視**: Web サービスを先に起動してから、`set_reporter(True)` で有効化する必要があります。

## 例

```python
from celestialflow import TaskStage, TaskGraph

# ノードの作成
stage_a = TaskStage("A", func=process_a, execution_mode="thread", stage_mode="thread")
stage_b = TaskStage("B", func=process_b, execution_mode="serial", stage_mode="thread")
stage_c = TaskStage("C", func=process_c, execution_mode="serial", stage_mode="thread")

# グラフの構築
graph = TaskGraph(schedule_mode="eager", log_level="INFO")
graph.set_stages(stages=[stage_a, stage_b, stage_c])
graph.connect([stage_a], [stage_b, stage_c])

# 設定
graph.set_reporter(True, host="127.0.0.1", port=5005)

# 開始
graph.start_graph({
    stage_a.get_tag(): range(100)
})
```
