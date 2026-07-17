# Graph モジュール

> 📅 最終更新日: 2026/07/16

Graph モジュールは CelestialFlow のコアスケジューリングシステムであり、タスクノード間の依存関係、実行フロー、ライフサイクルを管理します。柔軟なタスクグラフ（TaskGraph）の構築、分析、シリアライズ機能を提供します。

## モジュール概要

Graph モジュールはタスク実行の基本ユニットとそれらの関係を定義し、有向グラフを形成します。各ノードは `TaskStage` を表し、エッジはデータフローの依存関係を表します。このモジュールは、タスクが正しいトポロジカル順序で実行されることを保証し、並行処理、エラー処理、リソース管理を扱います。

### 公開エクスポートシンボル (`__all__`)

```python
from celestialflow.graph import (
    TaskChain,      # 線形タスクチェーン
    TaskComplete,   # 完全グラフ構造
    TaskCross,      # 多層クロス構造
    TaskGraph,      # コアタスクグラフ
    TaskGrid,       # 二次元グリッド構造
    TaskLoop,       # リング構造
    TaskWheel,      # ホイール構造
)
```

## ファイル説明

### コアファイル

1. **core_graph.py** (`TaskGraph`)
   - **役割**: コアスケジューラ。`TaskStage` ノードの依存関係、実行フロー、リソース割り当て、ライフサイクルを管理します
   - **主要機能**:
     - ノード間の依存関係の確立（`set_stages` / `connect`）
     - タスクグラフの実行（`eager` 一括起動 / `staged` 階層実行）
     - 実行時監視スナップショットとグローバル残り時間推定
     - 動的タスク注入（`put_stage_queue`）
     - エラー永続化と未消費タスク処理

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

3. **util_graph.py**
   - **役割**: 軽量な順序付き有向グラフと基礎グラフアルゴリズムツール
   - **主要関数**:
     - `OrderGraph`: 最小順序付き有向グラフ。安定したノード順序、入辺・出辺の隣接テーブルを維持
     - `is_dag()` / `topo_sort()`: DAG 判定とトポロジカルソート
     - `tarjan_scc()` / `get_condensation()`: 強連結成分分析と凝縮グラフ構築
     - `compute_node_levels()`: SCC 凝縮グラフに基づくノード階層計算

4. **util_serialize.py**
   - **役割**: タスクグラフ構造の JSON シリアライズとテキスト化
   - **主要関数**:
     - `build_structure_graph()`: ノード辞書、隣接テーブル、ソースノードから構造 JSON を構築
     - `format_structure_list_from_graph()`: 印刷可能なツリーテキストにフォーマット

## モジュール関連

### 内部関連
- `TaskGraph` は基底クラスであり、他のすべての構造はこれを継承します
- `TaskChain`、`TaskLoop` などは `TaskGraph` の特殊化実装です（`set_stages` / `connect` ロジックをカプセル化）
- `util_graph.py` はフレームワーク内部で統一して再利用される軽量グラフ構造と基礎グラフアルゴリズムを提供します
- `TaskGraph` は現在 `OrderGraph` に基づいてソースノード識別、DAG 判定、階層分析を行います
- シリアライズツールは実行時構造を JSON/テキストとして出力します

### 外部関連
- **Stage モジュールと**: `TaskGraph` は `TaskStage` ノードを管理し、各ノードは `start_stage` で起動します
- **Runtime モジュールと**: `TaskInQueue`/`TaskOutQueue` をノード間通信パイプとして使用します
- **Persistence モジュールと**: `LogSpout`/`FallbackSpout` を通じて永続化を実現します
- **Observability モジュールと**: `TaskReporter` を通じて `celestialflow-web` サービスに状態をプッシュし、注入命令を取得します

## 使用パターン

1. **タスクグラフの構築**: `TaskStage` ノードを作成 → `set_stages()` で登録 → `connect()` で依存関係を確立
2. **構造の選択**: 一般的なパターンには `TaskChain`/`TaskCross` などの事前定義構造を直接使用可能
3. **設定**: `set_reporter()` / `set_ctree()` で外部サービスを統合
4. **実行**: `start_graph()` を呼び出し
5. **監視**: `collect_runtime_snapshot()` と `get_status_snapshot()` で状態を取得

## 使用例

以下の例は graph モジュールの各種グラフ構造の構築と実行方法を示します。

### 基本 TaskGraph の構築

```python
from celestialflow import TaskGraph, TaskStage

# ステージ関数を定義
def stage_a_func(x: int) -> int:
    return x + 1

def stage_b_func(x: int) -> int:
    return x * 2

def stage_c_func(x: int) -> int:
    return x - 3

# ノードを作成
s1 = TaskStage("S1", func=stage_a_func, execution_mode="serial")
s2 = TaskStage("S2", func=stage_b_func, execution_mode="serial")
s3 = TaskStage("S3", func=stage_c_func, execution_mode="serial")

# DAG を構築: S1 -> S2 -> S3
graph = TaskGraph(name="MyGraph", schedule_mode="eager")
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# 実行
graph.start_graph({s1.get_name(): [1, 2, 3]})

# グラフ分析
analysis = graph.get_graph_analysis()
print(f"DAG か: {analysis['isDAG']}")
print(f"階層: {analysis['layersDict']}")
```

### TaskChain 線形チェーン

```python
from celestialflow import TaskChain, TaskStage

stages = [
    TaskStage("Clean", func=lambda x: x.strip().lower()),
    TaskStage("Parse", func=lambda x: int(x)),
    TaskStage("Compute", func=lambda x: x ** 2),
]

chain = TaskChain(name="DataPipeline", stages=stages, stage_mode="serial")
chain.start_graph({stages[0].get_name(): [" 10 ", " 20 ", " 30 "]})

print(f"チェーン状態: {chain.get_status_snapshot()}")
```

### TaskCross クロス層

```python
from celestialflow import TaskCross, TaskStage

# 2 層を定義
layer1 = [TaskStage("F1", func=lambda x: x * 2), TaskStage("F2", func=lambda x: x + 3)]
layer2 = [TaskStage("G1", func=lambda x: x ** 2), TaskStage("G2", func=lambda x: -x)]

cross = TaskCross(name="CrossPipeline", layers=[layer1, layer2], schedule_mode="eager")
cross.start_graph({layer1[0].get_name(): [1, 2], layer1[1].get_name(): [10, 20]})
print(cross.get_status_snapshot())
```

### TaskGrid グリッド

```python
from celestialflow import TaskGrid, TaskStage

s00 = TaskStage("A", func=lambda x: x)
s01 = TaskStage("B", func=lambda x: x + 1)
s10 = TaskStage("C", func=lambda x: x * 2)
s11 = TaskStage("D", func=lambda x: x * x)

grid = TaskGrid(name="GridPipeline", grid=[[s00, s01], [s10, s11]])
grid.start_graph({s00.get_name(): [1, 2]})
print(grid.get_status_snapshot())
```

### TaskLoop リンググラフ

```python
from celestialflow import TaskLoop, TaskStage

stages = [
    TaskStage("L1", func=lambda x: x + 1),
    TaskStage("L2", func=lambda x: x * 2),
    TaskStage("L3", func=lambda x: x - 1),  # L3 -> L1 でリングを形成
]

loop = TaskLoop(name="FeedbackLoop", stages=stages)
# リング構造では早期終了を防ぐため put_termination_signal=False を推奨
loop.start_graph({stages[0].get_name(): [10]}, put_termination_signal=False)
```

### TaskWheel ホイールグラフ

```python
from celestialflow import TaskWheel, TaskStage

center = TaskStage("Center", func=lambda x: f"processed: {x}")
ring = [TaskStage(f"R{i}", func=lambda x: f"ring-{i}: {x}") for i in range(3)]

wheel = TaskWheel(name="HubAndSpoke", center=center, ring=ring)
wheel.start_graph({center.get_name(): ["data"]})
```

## ベストプラクティス

- 線形フローには `TaskChain` を使用し、手動 `connect` は不要
- マルチパス並行パイプラインには `TaskCross` または手動組み合わせを使用
- 循環グラフ（`TaskLoop`/`TaskWheel`）では `put_termination_signal=False` を推奨し、外部注入で停止
- 外部監視システムとの連携が必要な場合は `set_reporter(True)` を有効化
- 複雑な DAG には `staged` モードを使用し、階層ごとのデバッグを容易に
