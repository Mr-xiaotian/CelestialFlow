# src/celestialflow/graph/core_graph.py

> 📅 最終更新日: 2026/09/24

`TaskGraph` は CelestialFlow のコアスケジューラであり、一連のタスクノード（`BaseTaskNode` 派生オブジェクト、パブリック API は `TaskExecutor`、`TaskSplitter`、`TaskRouter`）の依存関係、実行フロー、リソース割り当て、ライフサイクルを管理します。

> 注意: `TaskGraph` は単一回使用のオブジェクトです。一度 `start()` / `start_async()` / `run()` が完了した後、現在のインスタンスが安全にリセットされて再起動できることは保証されません。同じフローを繰り返し実行する必要がある場合は、新しい `TaskGraph` と関連するタスクノードを再作成してください。

## 主要データ構造

`TaskGraph` は内部で `node_dict: dict[str, AnyTaskNode]` を使用して全ノードのマッピングを保持し、キュー接続は `connect()` フェーズでノードの `connect_to()` を通じて確立されます。グラフ分析は内部で維持される `OrderGraph` インスタンス（`self.order_graph`）に基づき、その `out_edges` / `in_edges` は入辺・出辺隣接テーブルの参照ビューです。

インスタンス上のグラフ分析結果フィールド：

| フィールド | 型 | 説明 |
|------|------|------|
| `source_names` | `list[str]` | ソースノードリスト（`_build_analysis` によって計算） |
| `is_dag` | `bool` | 有向非巡回グラフかどうか |
| `layers_dict` | `dict[int, list[str]]` | 階層 → ノード名リスト |
| `_analysis_dirty` | `bool` | 分析キャッシュを再構築する必要があるか |

## 初期化

```python
class TaskGraph:
    def __init__(self, name: str, graph_mode: str = "serial"): ...
```

### パラメータ説明

- **name**: タスクグラフ名（必須）
- **graph_mode**: グラフ実行モード
  - `serial`（デフォルト）: 直列実行。階層（`layers_dict`）のトポロジカル順に従い逐層実行
  - `thread`: スレッド並行実行。各ノードが独立スレッドで起動
  - `async`: 非同期並行実行。実行中のイベントループコンテキストでの呼び出しが必要（[`start_async`](#start_async) 参照）

`__init__` は `_set_name`、`set_graph_mode`、`set_reporter(NullTaskReporter())`、`set_ctree(LocalEventClient())`、`_init_state()` を順に呼び出します。

## グラフ構築

### set_nodes

```python
def set_nodes(self, nodes: list[AnyTaskNode]) -> None:
    """
    ノードをタスクグラフに追加します。ノードを登録し、OrderGraph に書き込み、グラフレベルのイベントクライアントを注入します。

    :param nodes: 追加するノードのリスト
    :raises DuplicateNodeError: ノード名が重複している場合
    """
```

登録後、`_analysis_dirty` は `True` に設定されます。

### connect

```python
def connect[R](
    self,
    from_nodes: list[AnyTaskNode],
    to_nodes: list[AnyTaskNode],
) -> None:
    """
    ハイパーエッジ接続を確立します: from_nodes の各ノードが to_nodes の各ノードに接続されます。
    内部で from_node.connect_to(to_node) を呼び出してキュー接続を完了し、order_graph に辺を追加します。

    :param from_nodes: 上流ノードリスト
    :param to_nodes: 下流ノードリスト
    :raises NodeNotFoundError: いずれかの端点ノードが未登録
    """
```

## 設定メソッド

### _set_name

```python
def _set_name(self, name: str) -> None:
    """タスクグラフ名を設定し、graph_id = f"{name}@{int(time.time() * 1000)}" を生成します。"""
```

### set_graph_mode

```python
def set_graph_mode(self, graph_mode: str) -> None:
    """
    グラフ実行モードを設定します。指定可能な値は 'serial'、'thread'、'async' です。

    :raises InvalidOptionError: graph_mode が有効な集合に含まれない場合
    """
```

### set_node_execution_mode

```python
def set_node_execution_mode(self, execution_mode: str) -> None:
    """
    全ノードの execution_mode を一括設定します（'serial'、'thread'、'async'）。
    _build_analysis() をトリガーして分析データを再構築します。
    """
```

### set_reporter

```python
def set_reporter(self, reporter: ReporterProtocol) -> None:
    """
    タスクグラフにバインドされるレポーターを設定します。

    :param reporter: レポーターインスタンス
    """
```

### set_ctree

```python
def set_ctree(self, ctree_client: EventClient) -> None:
    """
    タスクグラフ共有のイベントクライアントを設定します。
    渡されると、現在のグラフ内の全ノードに同期して下位配信されます。
    """
```

> デフォルトでは、`TaskGraph` は内部で `LocalEventClient()` を使用してローカルのインクリメンタルイベント ID を生成するため、`celestialtree` がインストールされていなくても、コア実行リンクは正常に動作します。
>
> イベントを CelestialTree に報告したい場合は、まず `celestialtree` を追加インストールし、対応するクライアントインスタンスを自身で構築して `set_ctree()` に渡す必要があります。

## グラフ分析

### _ensure_analysis

```python
def _ensure_analysis(self) -> None:
    """オンデマンドでグラフ分析キャッシュを再構築します: _analysis_dirty が True の場合のみ _build_analysis() を呼び出します。"""
```

### _build_analysis

```python
def _build_analysis(self) -> None:
    """
    タスクグラフを分析し、ソースノード、DAG かどうか、階層情報を計算します。

    :raises ConfigurationError: serial モードでグラフに環（非 DAG）が含まれる場合に発生
    """
```

分析プロセス：`source_nodes()` → `is_dag()` → `compute_node_levels()` → `cluster_by_value_sorted()` で `layers_dict` を取得；その後、グラフに環が含まれかつ `graph_mode == "serial"` の場合、`ConfigurationError` を送出し、`thread` または `async` への切り替えを促します。

### put_source_signal

```python
def put_source_signal(self) -> None:
    """すべてのソースノードのキューに終了シグナルを入れます。"""
```

## 起動実行

### run

```python
def run(
    self,
    init_tasks_dict: dict[str, Iterable[Any]],
    *,
    if_put_signal: bool = True,
) -> None:
    """
    タスクグラフを実行します。フロー：
    1. _build_analysis() を呼び出してグラフ分析を構築
    2. funnel_scope() の下で、init_tasks_dict 内の各タスクを対応するノードに注入（node.put_task）
    3. if_put_signal=True の場合、ソースノードに自動的に終了シグナルを注入
    4. start() を呼び出して実行を起動
    """
```

### run_async

```python
async def run_async(
    self,
    init_tasks_dict: dict[str, Iterable[Any]],
    *,
    if_put_signal: bool = True,
) -> None:
    """run() の非同期バージョン。注入後に start_async() を呼び出します。"""
```

### restore_db

```python
def restore_db(
    self,
    db_path: str | Path,
    statuses: Iterable[str] | None = None,
    *,
    filter_by_error_type: bool = False,
    if_put_signal: bool = True,
) -> None:
    """
    sqlite 永続化ライブラリからタスクを読み込み、永続化レコード内のノード名でグループ化してタスクグラフを起動します。

    :param db_path: sqlite データベースファイルパス
    :param statuses: レコードステータスフィルタリスト。デフォルト ``["failed", "pending"]``
    :param filter_by_error_type: 各ノードの ``retry_exceptions`` で ``error_type`` をフィルタリングするかどうか。デフォルト ``False``
    :param if_put_signal: 復元タスクの注入後にすべてのソースノードへ終了シグナルを再送するかどうか。デフォルト True
    """
```

このメソッドは内部で `load_tasks_grouped_by_stage()` を呼び出して永続化タスクレコードを読み込み、
`node.metrics.get_retry_error_type_names()` で回復可能なエラータイプをフィルタリングし（`pending` レコードは常に保持）、
最終的に `run()` を再利用して実行します。

### ライフサイクル制約

- `TaskGraph` は起動プロセス中に実行時キュー接続、先行バインディング、スレッド参照、状態スナップショットを確立します。
- これらの実行時リソースは設計上単一の完全実行を対象としており、実行終了後に安全にクリアされて再利用されることは保証されません。
- 同じトポロジを再実行する必要がある場合は、同一インスタンスの `run()` を再度呼び出すのではなく、グラフオブジェクトとノードオブジェクトを再インスタンス化することを推奨します。

```python
graph = TaskGraph(name="MyGraph", graph_mode="thread")
graph.set_nodes(nodes=[node_a, node_b])
graph.connect([node_a], [node_b])
graph.run({node_a.get_name(): [1, 2, 3, 4, 5]})
```

### start

```python
def start(self) -> None:
    """
    タスクグラフを起動します（同期エントリ）。
    graph_mode に応じて _execute_nodes_serial() または _execute_nodes_thread() を選択します。
    起動と終了処理の段階で発生した例外は ExceptionGroup として集約されて送出されます。
    """
```

### start_async

```python
async def start_async(self) -> None:
    """
    タスクグラフを非同期で起動します。graph_mode='async' が必要。そうでない場合は InvalidOptionError を送出します。
    同期 start() との違い：
    - async 実行モードのノードはコルーチン（node.start_async()）を通り、ノード内部で asyncio.run を再度呼び出しません；
    - serial / thread 実行モードのノードは asyncio.to_thread により独立したスレッドで実行されます。
    """
```

### _prepare_start / _finish_start

```python
def _prepare_start(self) -> None:
    """
    起動前準備：グラフ起動ログ（get_log_inlet().graph_start）を記録し、reporter.start() を呼び出します。
    本メソッドはスレッドやファイルハンドルなどの実行時リソースを作成します。
    """


def _finish_start(self, start_perf: float) -> list[Exception]:
    """
    起動後の終了処理：全ノードを走査して drain_task_queue() を呼び出し未消費タスクを収集し、
    reporter を停止し、グラフ終了ログを記録し、スレッド参照をクリーンアップして、収集した例外リストを返します。
    """
```

`lifecycle` / `log` spout の起動と停止は外側の `funnel_scope()` によって統一的に管理されます。

### _execute_nodes_serial / _execute_nodes_thread / _execute_nodes_async

```python
def _execute_nodes_serial(self) -> None:
    """階層（layers_dict）のトポロジカル順に従い、層ごとに、ノードごとに直列実行（層内は登録順）。"""


def _execute_nodes_thread(self) -> None:
    """各ノードを独立したデーモンスレッドで起動し、最後に一括 join。"""


async def _execute_nodes_async(self) -> None:
    """グラフ全体を並行実行（asyncio.gather）。"""
```

### _execute_node / _execute_node_async

```python
def _execute_node(self, node: AnyTaskNode) -> None:
    """
    同期グラフ起動パスで単一ノードを実行します。
    - async ノードは asyncio.run(node.start_async())
    - その他のノードは node.start()
    """


async def _execute_node_async(self, node: AnyTaskNode) -> None:
    """
    単一ノードを非同期実行：async はコルーチン、それ以外は asyncio.to_thread(node.start)。
    """
```

## 照会インターフェース

| メソッド | 戻り値型 | 説明 |
|------|---------|------|
| `get_graph_id()` | `str` | 現在のタスクグラフインスタンスの一意識別子を取得 |
| `get_nodes()` | `list[str]` | 登録順に全ノード名を返す |
| `get_edges()` | `dict[str, list[str]]` | 出辺隣接テーブル（内部 `OrderGraph` との共有参照。呼び出し側は読み取り専用とすべき） |
| `get_node_meta()` | `dict[str, dict[str, Any]]` | 各ノードの構築期メタ情報 |
| `get_source_nodes()` | `list[str]` | ソースノード名のリスト（オンデマンドでグラフ分析をトリガー） |
| `get_graph_analysis()` | `dict` | グラフ分析情報（graphId, graphMode, name, startTime, className, isDAG, layersDict） |
| `get_structure_list()` | `list[str]` | 枠線付きのフォーマット済みツリーテキスト |
| `get_order_graph()` | `OrderGraph` | 内部の順序付き有向グラフインスタンス |
| `get_lifecycle_path()` | `Path` | タスクライフサイクル永続化 sqlite ファイルの絶対パス。未設定時は空 Path を返す |

### get_node_meta の説明

各ノードの構築期メタ情報を返します。これらのフィールドは reporter の起動前に凍結されるため、グラフ構造とともに一度だけ報告され、毎回の状態プッシュには含まれません：

```python
{
    node_name: {
        "class_name": ...,      # ノードクラス名
        "execution_mode": ...,  # 実行モード
        "max_workers": ...,     # 最大並行ワーカー数
    }
}
```

### get_graph_analysis の説明

`get_graph_analysis()` は以下のフィールドを含む辞書を返します：

```python
{
    "graphId": self.graph_id,
    "graphMode": self.graph_mode,
    "name": self.name,
    "startTime": self.start_time,
    "className": self.__class__.__name__,
    "isDAG": self.is_dag,
    "layersDict": self.layers_dict,
}
```

### 実行時状態の収集

`TaskGraph` 自体は実行時スナップショットを集約しません。各ノードは `BaseTaskNode.get_snapshot()` を通じて自身の状態を収集し、
`TaskReporter` が状態プッシュ周期でノードを走査してこれを呼び出します；グローバルな `total_*` などの派生指標はフロントエンド
（`celestialflow-web`）が集約して計算します。

## ライフサイクル図

```mermaid
flowchart TD
    INIT[__init__] --> INIT_STATE[_init_state]
    INIT_STATE --> BUILD[set_nodes + connect]
    BUILD --> PREPARE[_prepare_start]
    PREPARE --> START[start / start_async]
    START -->|serial| SER[_execute_nodes_serial]
    START -->|thread| THR[_execute_nodes_thread]
    START -->|async| ASY[_execute_nodes_async]
    SER --> FINISH[_finish_start]
    THR --> FINISH
    ASY --> FINISH
    FINISH -->|drain_task_queue| DRAIN[未消費タスクの収集]
    DRAIN --> END[グラフ実行完了]

    RUN[run / run_async] -->|初期タスク注入| PUT[node.put_task]
    RUN -->|終了シグナル注入| SIGNAL[put_source_signal]
```

## グラフ実行モード詳解

### serial モード

```
layers_dict の階層トポロジカル順に従い、層ごとに node.start() を同期実行 → データがキューを通じてフロー → 終了シグナル到達後に停止
```

- 階層（トポロジカル順）ごとに同期実行。層内は登録順
- デフォルトモード
- 適用シーン：デバッグ、直列パイプライン

### thread モード

```
各ノードに対して独立スレッドを起動 → node.start() → 全スレッドを join
```

- 並列度を最大化
- 適用シーン：CPU/IO 混在型の並行パイプライン

### async モード

```
全ノードを非同期実行（asyncio.gather）→ 既存のイベントループ内で start_async() を呼び出す必要あり
```

- グラフ全体を並行コルーチン実行
- `serial` / `thread` モードのノードは `asyncio.to_thread` により独立スレッドで実行され、イベントループをブロックしない
- 適用シーン：他の非同期システムとの統合が必要な場合

## 非 DAG グラフの注意事項

循環グラフ（`TaskLoop` / `TaskWheel` など）に対し、`graph_mode='serial'` でグラフに循環（非 DAG）がある場合、
`_build_analysis` は `ConfigurationError` を送出し、`thread` または `async` モードへの切り替えを要求します。

`thread` / `async` モードで循環グラフを使用する場合、`run` 実行時に `if_put_signal=False` を設定し、
外部から明示的に `TerminationSignal` を注入して停止タイミングを制御することを推奨します。
そうしないと、終了シグナルによって一部のノードが上流データを受信する前に早期終了する可能性があります。

```python
graph.run({"source": tasks}, if_put_signal=False)
# その後 node.put_task または外部から手動で TerminationSignal を注入
```

## 未消費タスク処理

`_finish_start()` 内で `node_dict` を反復し、各ノードの `drain_task_queue()` を呼び出して全残存タスクを収集し、
それらを `UnconsumedError` としてマークし、`get_lifecycle_spout`（`LifecycleSpout`）を通じて日付別に組織された lifecycle
sqlite 永続化ファイルに失敗情報を記録します。
