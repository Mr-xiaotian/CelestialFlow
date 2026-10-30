# src/celestialflow/graph/__init__.py

> 📅 最終更新日: 2026/10/30

Graph モジュールは CelestialFlow のコアスケジューリングシステムであり、タスクノード間の依存関係、実行フロー、ライフサイクルを管理します。柔軟なタスクグラフの構築と分析機能を提供します。

## モジュール概要

Graph モジュールはタスク実行の基本ユニットとそれらの関係を定義し、有向グラフを形成します。各ノードは `celestialflow.node` で定義された `BaseTaskNode` の派生オブジェクト（パブリック API は `TaskExecutor`、`TaskSplitter`、`TaskRouter`）であり、エッジはデータフローの依存関係を表します。このモジュールは、タスクが正しいトポロジカル順序で実行されることを保証し、並行処理、エラー処理、リソース管理を扱います。

### 公開エクスポートシンボル (`__all__`)

```python
from celestialflow.graph import (
    TaskChain,  # 線形タスクチェーン
    TaskComplete,  # 完全グラフ構造
    TaskCross,  # 多層クロス構造
    TaskGraph,  # コアタスクグラフ
    TaskGrid,  # 二次元グリッド構造
    TaskLoop,  # リング構造
    TaskWheel,  # ホイール構造
)
```

`__all__ = ["TaskChain", "TaskComplete", "TaskCross", "TaskGraph", "TaskGrid", "TaskLoop", "TaskWheel"]`

## ファイル説明

### コアファイル

1. **core_graph.py** (`TaskGraph`)
   - **役割**: コアスケジューラ。タスクノード（`BaseTaskNode` 派生オブジェクト）の依存関係、実行フロー、ライフサイクルを管理します
   - **主要機能**:
     - ノード間の依存関係の確立（`set_nodes` / `connect`）
     - タスクグラフの実行（`start` / `start_async`、`graph_mode` に基づく serial/thread/async 実行）
     - ノードの実行モード一括設定（`set_node_execution_mode`）と共有イベントクライアントの設定（`set_ctree`）
     - グラフレベル観測者の登録（`add_observer`）とクエリ（`get_observers`）
     - グラフ分析（`_build_analysis` による遅延再構築：ソースノード識別、DAG 判定、階層計算。公開エントリは `get_source_nodes()` / `is_dag()` / `get_layers()`）
     - 初期タスクと永続化タスクの注入（`run` / `run_async` / `restore_db` / `inject_tasks` / `inject_terminations`）。実行エントリは `log_level` と `report`（`ReportConfig`）パラメータをサポート

2. **core_structure.py**（事前定義グラフ構造）
   - **役割**: 6 種類の事前定義タスクグラフ構造を提供し、一般的なパターンを簡素化します
   - **含まれる構造**:
     - `TaskChain`: 線形タスクチェーン。ノードを順序通りに接続
     - `TaskLoop`: リング構造。ノードを首尾接続
     - `TaskCross`: 多層クロス構造。層内並行、層間全結合
     - `TaskComplete`: 完全グラフ。各ノードが他の全ノードに接続
     - `TaskWheel`: スポーク構造。中心ノードがリング上の全ノードに接続
     - `TaskGrid`: 二次元グリッド。ノードが右隣と下隣に接続

### ユーティリティファイル

3. **util_order_graph.py**
   - **役割**: 軽量な順序付き有向グラフと基礎グラフアルゴリズムツール
   - **主要内容**:
     - `OrderGraph`: 最小順序付き有向グラフ。安定したノード順序、入辺・出辺の隣接テーブルを維持
     - `is_dag()` / `topo_sort()`: DAG 判定とトポロジカルソート
     - `tarjan_scc()` / `get_condensation()`: 強連結成分分析と凝縮グラフ構築
     - `source_sccs()` / `source_nodes()`: ソース SCC を特定し代表的なソースノードを抽出
     - `compute_node_levels()`: SCC 凝縮グラフに基づくノード階層計算

> 説明：グラフ構造のツリー形式テキストレンダリング（`render_structure_list`）は本モジュールから `persist/util_render.py` へ移行されました。Graph モジュールはもはやレンダリングロジックを保持しません。

## モジュール連携

### 内部連携
- `TaskGraph` は基底クラスであり、他のすべての構造はこれを継承します
- `TaskChain`、`TaskLoop` などは `TaskGraph` の特殊化実装です（`set_nodes` / `connect` ロジックをカプセル化）
- `util_order_graph.py` はフレームワーク内部で統一して再利用される軽量グラフ構造と基礎グラフアルゴリズムを提供します
- `TaskGraph` は現在 `OrderGraph` に基づいてソースノード識別、DAG 判定、階層分析を行います。分析結果は `_analysis_dirty` フラグによって駆動される遅延再構築で生成され、公開読み取りエントリは `get_source_nodes()` / `is_dag()` / `get_layers()` です

### 外部連携
- **Node モジュールとの連携**: タスクグラフノード（`TaskExecutor` / `TaskSplitter` / `TaskRouter`）は `celestialflow.node` が提供し、`TaskGraph` は組み立て・接続・スケジューリングのみを担当
- **Runtime モジュールとの連携**: ノード間通信パイプとして `TaskInQueue`/`TaskOutQueue` を使用
- **Observer モジュールとの連携**: `add_observer()` でグラフレベル観測者を登録し、グラフ内の全ノードのイベントを受信。実行時リソースは `run_graph_resources` で一元管理
- **Persistence モジュールとの連携**: 永続化エントリ（lifecycle / log）を通じてタスクの永続化と復元を実現（`restore_db`）

## 使用パターン

1. **タスクグラフの構築**: `TaskExecutor` ノードを作成（必要に応じて `TaskSplitter` / `TaskRouter` を使用）→ `set_nodes()` で登録 → `connect()` で依存関係を確立
2. **構造の選択**: 一般的なパターンには `TaskChain`/`TaskCross` などの事前定義構造を直接使用可能
3. **設定**: `set_ctree()` でイベントクライアントを注入、`add_observer()` でグラフレベル観測者を登録
4. **実行**: `run()` または `run_async()` を呼び出します。`log_level`（デフォルト `"INFO"`）でログレベルを設定でき、`report=ReportConfig(...)` でリモートレポートを有効化できます（デフォルト `None` はレポートなし）

## 使用例

以下の例は graph モジュールの各種グラフ構造の構築と実行方法を示します。

### 基本 TaskGraph の構築

```python
from celestialflow import TaskGraph, TaskExecutor


# ステージ関数を定義
def stage_a_func(x: int) -> int:
    return x + 1


def stage_b_func(x: int) -> int:
    return x * 2


def stage_c_func(x: int) -> int:
    return x - 3


# ノードを作成
s1 = TaskExecutor("S1", func=stage_a_func, execution_mode="serial")
s2 = TaskExecutor("S2", func=stage_b_func, execution_mode="serial")
s3 = TaskExecutor("S3", func=stage_c_func, execution_mode="serial")

# DAG を構築: S1 -> S2 -> S3
graph = TaskGraph(name="MyGraph", graph_mode="thread")
graph.set_nodes([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# 実行
graph.run({s1.get_name(): [1, 2, 3]})

# グラフ分析（初回読み取り時に必要に応じて計算）
print(f"ソースノード: {graph.get_source_nodes()}")
print(f"DAG かどうか: {graph.is_dag()}")  # is_dag はメソッドであることに注意
print(f"階層: {graph.get_layers()}")
print(f"ノードリスト: {graph.get_nodes()}")
print(f"エッジ隣接テーブル: {graph.get_edges()}")
```

### ログレベルとリモートレポートの有効化

```python
from celestialflow import TaskExecutor, TaskGraph
from celestialflow.runtime import ReportConfig

node = TaskExecutor("Only", func=lambda x: x + 1)
graph = TaskGraph(name="Reported", graph_mode="thread")
graph.set_nodes([node])

graph.run(
    {node.get_name(): [1, 2, 3]},
    log_level="DEBUG",
    report=ReportConfig(url="http://127.0.0.1:5005"),
)
```

> `report` を使用する前に、そのアドレスで受信サービスが動作していることを確認してください。`report=None`（デフォルト）を渡すとレポートは完全に無効になります。

### TaskChain 線形チェーン

```python
from celestialflow import TaskChain, TaskExecutor

nodes = [
    TaskExecutor("Clean", func=lambda x: x.strip().lower()),
    TaskExecutor("Parse", func=lambda x: int(x)),
    TaskExecutor("Compute", func=lambda x: x**2),
]

chain = TaskChain(name="DataPipeline", nodes=nodes, graph_mode="thread")
chain.run({nodes[0].get_name(): [" 10 ", " 20 ", " 30 "]})

# ノードとソースを確認
print(chain.get_nodes())
```

### TaskCross クロス層

```python
from celestialflow import TaskCross, TaskExecutor

# 2 層を定義
layer1 = [
    TaskExecutor("F1", func=lambda x: x * 2),
    TaskExecutor("F2", func=lambda x: x + 3),
]
layer2 = [
    TaskExecutor("G1", func=lambda x: x**2),
    TaskExecutor("G2", func=lambda x: -x),
]

cross = TaskCross(name="CrossPipeline", layers=[layer1, layer2], graph_mode="thread")
cross.run({layer1[0].get_name(): [1, 2], layer1[1].get_name(): [10, 20]})
```

### TaskGrid グリッド

```python
from celestialflow import TaskGrid, TaskExecutor

s00 = TaskExecutor("A", func=lambda x: x)
s01 = TaskExecutor("B", func=lambda x: x + 1)
s10 = TaskExecutor("C", func=lambda x: x * 2)
s11 = TaskExecutor("D", func=lambda x: x * x)

grid = TaskGrid(name="GridPipeline", grid=[[s00, s01], [s10, s11]])
grid.run({s00.get_name(): [1, 2]})
```

### TaskLoop リンググラフ

```python
from celestialflow import TaskLoop, TaskExecutor

nodes = [
    TaskExecutor("L1", func=lambda x: x + 1),
    TaskExecutor("L2", func=lambda x: x * 2),
    TaskExecutor("L3", func=lambda x: x - 1),  # L3 -> L1 でリングを形成
]

loop = TaskLoop(name="FeedbackLoop", nodes=nodes)
# リンググラフは直接 run できません（永久にブロックされます）。外部条件が満たされた後に終了シグナルを注入する必要があります：
# loop.inject_terminations([n.get_name() for n in nodes])
# loop.run({nodes[0].get_name(): [10]}, if_put_signal=False)

print(loop.is_dag())  # False
print(loop.get_layers())  # 同一リング内のノードは階層を共有
```

### TaskWheel ホイールグラフ

```python
from celestialflow import TaskWheel, TaskExecutor

center = TaskExecutor("Center", func=lambda x: f"processed: {x}")


def make_ring_node(index: int) -> TaskExecutor:
    # ノードコールバックは位置引数を 1 つだけ受け取る必要があるため、クロージャで添字を捕捉
    def handle(x: str) -> str:
        return f"ring-{index}: {x}"

    return TaskExecutor(f"R{index}", func=handle)


ring = [make_ring_node(i) for i in range(3)]
wheel = TaskWheel(name="HubAndSpoke", center=center, ring=ring)

# 同様にリンググラフです：実行前に外部からの終了注入を自分で用意する必要があります
print(wheel.get_nodes())  # ['Center', 'R0', 'R1', 'R2']
print(wheel.is_dag())  # False
```

## ベストプラクティス

- 線形フローには `TaskChain` を使用し、手動 `connect` は不要
- マルチパス並行パイプラインには `TaskCross` または手動組み合わせを使用
- 循環グラフ（`TaskLoop` / `TaskWheel` / `TaskComplete`）は `serial` モードでは使用できず、`run()` は永久にブロックされるため、外部条件が満たされた後に `inject_terminations()` を呼び出して終了シグナルを注入する必要があります
- グラフ内のイベントを監視・受信する必要がある場合は `add_observer()` でグラフレベル観測者を登録
- 非同期実行には `TaskGraph` の `graph_mode="async"` を使用し、`start_async()` / `run_async()` で起動
- グラフ分析結果は `get_source_nodes()` / `is_dag()` / `get_layers()` で読み取ります（いずれもメソッド呼び出し）。私有化された `_source_names` / `_is_dag` / `_layers_dict` にアクセスしないでください
