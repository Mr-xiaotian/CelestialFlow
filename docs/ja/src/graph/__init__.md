# Graph モジュール

> 📅 最終更新日: 2026/09/09

Graph モジュールは CelestialFlow のコアスケジューリングシステムであり、タスクノード間の依存関係、実行フロー、ライフサイクルを管理します。柔軟なタスクグラフの構築、分析、レンダリング機能を提供します。

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

## ファイル説明

### コアファイル

1. **core_graph.py** (`TaskGraph`)
   - **役割**: コアスケジューラ。タスクノード（`BaseTaskNode` 派生オブジェクト）の依存関係、実行フロー、リソース割り当て、ライフサイクルを管理します
   - **主要機能**:
     - ノード間の依存関係の確立（`set_nodes` / `connect`）
     - タスクグラフの実行（`start` / `start_async`、`graph_mode` に基づく serial/thread/async 実行）
     - 実行時監視スナップショットとグローバル残り時間推定（`collect_runtime_snapshot`）
     - 初期タスクと永続化タスクの注入（`run` / `run_async` / `restore_db`）
     - エラー永続化と未消費タスク処理（`drain_task_queue`）

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
     - `compute_node_levels()`: SCC 凝縮グラフに基づくノード階層計算

4. **util_render.py**
   - **役割**: グラフ構造を枠線付きツリーテキストリストにレンダリング
   - **主要関数**:
     - `render_structure_list()`: ノード辞書、隣接テーブル、ソースノードから枠線付きツリーテキストを生成

## モジュール連携

### 内部連携
- `TaskGraph` は基底クラスであり、他のすべての構造はこれを継承します
- `TaskChain`、`TaskLoop` などは `TaskGraph` の特殊化実装です（`set_nodes` / `connect` ロジックをカプセル化）
- `util_order_graph.py` はフレームワーク内部で統一して再利用される軽量グラフ構造と基礎グラフアルゴリズムを提供します
- `TaskGraph` は現在 `OrderGraph` に基づいてソースノード識別、DAG 判定、階層分析を行います
- `util_render.py` は実行時構造を枠線付きツリーテキストリストとして出力します

### 外部連携
- **Node モジュールとの連携**: タスクグラフノード（`TaskExecutor` / `TaskSplitter` / `TaskRouter`）は `celestialflow.node` が提供し、`TaskGraph` は組み立て・接続・スケジューリングのみを担当
- **Runtime モジュールとの連携**: ノード間通信パイプとして `TaskInQueue`/`TaskOutQueue` を使用
- **Persistence モジュールとの連携**: `LifecycleSpout` により永続化を実現
- **Observability モジュールとの連携**: `TaskReporter` により `celestialflow-web` サービスに状態をプッシュし、注入命令をプル

## 使用パターン

1. **タスクグラフの構築**: `TaskExecutor` ノードを作成（必要に応じて `TaskSplitter` / `TaskRouter` を使用）→ `set_nodes()` で登録 → `connect()` で依存関係を確立
2. **構造の選択**: 一般的なパターンには `TaskChain`/`TaskCross` などの事前定義構造を直接使用可能
3. **設定**: `set_reporter()` / `set_ctree()` で外部サービスを統合
4. **実行**: `run()` または `run_async()` を呼び出す
5. **監視**: `collect_runtime_snapshot()` で状態スナップショットを取得

## 使用例

以下の例は graph モジュールの各種グラフ構造の構築と実行方法を示します。

### 基本 TaskGraph の構築

```python
from celestialflow import TaskGraph, TaskExecutor


# ノード関数を定義
def node_a_func(x: int) -> int:
    return x + 1


def node_b_func(x: int) -> int:
    return x * 2


def node_c_func(x: int) -> int:
    return x - 3


# ノードを作成
n1 = TaskExecutor("N1", func=node_a_func, execution_mode="serial")
n2 = TaskExecutor("N2", func=node_b_func, execution_mode="serial")
n3 = TaskExecutor("N3", func=node_c_func, execution_mode="serial")

# DAG を構築: N1 -> N2 -> N3
graph = TaskGraph(name="MyGraph", graph_mode="thread")
graph.set_nodes([n1, n2, n3])
graph.connect([n1], [n2])
graph.connect([n2], [n3])

# 実行
graph.run({n1.get_name(): [1, 2, 3]})

# グラフ分析
analysis = graph.get_graph_analysis()
print(f"DAG か: {analysis['isDAG']}")
print(f"階層: {analysis['layersDict']}")
```

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

# 監視：collect_runtime_snapshot でランタイムスナップショットを1回収集
snapshot, ts = chain.collect_runtime_snapshot()
print(f"スナップショットタイムスタンプ: {ts}")
print(f"ノード 0 のスナップショット: {snapshot[nodes[0].get_name()]}")
```

### TaskCross クロス層

```python
from celestialflow import TaskCross, TaskExecutor

# 2 層を定義
layer1 = [TaskExecutor("F1", func=lambda x: x * 2), TaskExecutor("F2", func=lambda x: x + 3)]
layer2 = [TaskExecutor("G1", func=lambda x: x**2), TaskExecutor("G2", func=lambda x: -x)]

cross = TaskCross(name="CrossPipeline", layers=[layer1, layer2], graph_mode="thread")
cross.run({layer1[0].get_name(): [1, 2], layer1[1].get_name(): [10, 20]})
print(cross.collect_runtime_snapshot())
```

### TaskGrid グリッド

```python
from celestialflow import TaskGrid, TaskExecutor

n00 = TaskExecutor("A", func=lambda x: x)
n01 = TaskExecutor("B", func=lambda x: x + 1)
n10 = TaskExecutor("C", func=lambda x: x * 2)
n11 = TaskExecutor("D", func=lambda x: x * x)

grid = TaskGrid(name="GridPipeline", grid=[[n00, n01], [n10, n11]])
grid.run({n00.get_name(): [1, 2]})
print(grid.collect_runtime_snapshot())
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
# リング構造では早期終了を防ぐため if_put_signal=False を推奨
loop.run({nodes[0].get_name(): [10]}, if_put_signal=False)
```

### TaskWheel ホイールグラフ

```python
from celestialflow import TaskWheel, TaskExecutor

center = TaskExecutor("Center", func=lambda x: f"processed: {x}")
ring = [TaskExecutor(f"R{i}", func=lambda x: f"ring-{i}: {x}") for i in range(3)]

wheel = TaskWheel(name="HubAndSpoke", center=center, ring=ring)
wheel.run({center.get_name(): ["data"]})
```

## ベストプラクティス

- 線形フローには `TaskChain` を使用し、手動 `connect` は不要
- マルチパス並行パイプラインには `TaskCross` または手動組み合わせを使用
- 循環グラフ（`TaskLoop`/`TaskWheel`）では `if_put_signal=False` を推奨し、外部注入で停止
- 外部監視システムとの連携が必要な場合は `set_reporter()` を使用
- 非同期実行には `TaskGraph` の `graph_mode="async"` を使用し、`start_async()` / `run_async()` で起動
