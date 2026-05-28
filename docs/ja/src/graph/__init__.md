# Graph モジュール

> 📅 最終更新日: 2026/05/28

Graph モジュールは CelestialFlow のコアスケジューリングシステムであり、タスクノード間の依存関係、実行フロー、ライフサイクルの管理を担当します。柔軟なタスクグラフの構築、分析、シリアライズ機能を提供します。

## モジュール概要

Graph モジュールはタスク実行の基本単位とその関係を定義し、有向グラフを形成します。各ノードは `TaskStage` を表し、エッジはデータフロー依存関係を表します。このモジュールはタスクが正しいトポロジカル順序で実行されることを保証し、並行処理、エラーハンドリング、リソース管理を処理します。

## ファイル説明

### コアファイル

1. **core_graph.py** (`TaskGraph`)
   - **役割**: コアスケジューラ。`TaskStage` ノードの依存関係、実行フロー、リソース割り当て、ライフサイクルを管理
   - **主要機能**:
     - ノード間の依存関係の確立（`set_stages` / `connect`）
     - タスクグラフの実行（`eager` 一斉起動 / `staged` レイヤー実行）
     - ランタイム監視スナップショットとグローバル残り時間の推定
     - 動的タスク注入（`put_stage_queue`）
     - エラー永続化と未消費タスクの処理

2. **core_structure.py**（定義済みグラフ構造）
   - **役割**: 一般的なパターンを簡素化する6つの定義済みタスクグラフ構造を提供
   - **含まれる構造**:
     - `TaskChain`: 線形タスクチェーン、ノードが順次接続
     - `TaskLoop`: リング構造、ノードが首尾接続
     - `TaskCross`: 多層クロス構造、層内並列、層間全結合
     - `TaskComplete`: 完全グラフ、各ノードが他の全ノードに接続
     - `TaskWheel`: ホイールスポーク構造、中心ノードが全リングノードに接続
     - `TaskGrid`: 2D グリッド、ノードが右と下の隣接に接続

### ユーティリティファイル

3. **util_analysis.py**
   - **役割**: `networkx` ベースのグラフ分析ツール
   - **主要関数**:
     - `build_networkx_graph()`: 隣接リストとランタイム情報から `DiGraph` を構築
     - `find_source_nodes()`: 入次数 0 のソースノードを検出
     - `compute_node_levels()`: ノードレベルを計算（DAG と循環グラフ対応）

4. **util_serialize.py**
   - **役割**: タスクグラフ構造の JSON シリアライズとテキスト化
   - **主要関数**:
     - `build_structure_graph()`: ソースノードから再帰的に構造 JSON を構築
     - `_build_structure_subgraph()`: サブグラフを再帰的に構築（内部関数）
     - `format_structure_list_from_graph()`: 印刷可能なツリー形式テキストにフォーマット

## モジュール関連

### 内部関連
- `TaskGraph` は基底クラスであり、他のすべての構造はこれを継承
- `TaskChain`、`TaskLoop` などは `TaskGraph` の特化実装（`set_stages` / `connect` ロジックをカプセル化）
- 分析ツールはグラフ理論計算に `networkx` に依存
- シリアライズツールはランタイム構造を JSON/テキストとして出力

### 外部関連
- **Stage モジュール**: `TaskGraph` は `TaskStage` ノードを管理。各ノードは `start_stage` で起動
- **Runtime モジュール**: ノード間通信パイプとして `TaskInQueue`/`TaskOutQueue` を使用
- **Persistence モジュール**: `LogSpout`/`FailSpout` で永続化
- **Observability モジュール**: `TaskReporter` で Web UI に状態をプッシュ

## 使用パターン

1. **タスクグラフの構築**: `TaskStage` ノードを作成 → `set_stages()` で登録 → `connect()` で依存関係を確立
2. **構造の選択**: 一般的なパターンには `TaskChain`/`TaskCross` などの定義済み構造を使用
3. **設定**: `set_reporter()` / `set_ctree()` で外部サービスを統合
4. **実行**: `start_graph()` またはサブクラスの `start_chain()`/`start_cross()` などを呼び出し
5. **監視**: `collect_runtime_snapshot()` と `get_graph_summary()` で状態を確認

## 使用例

以下に、さまざまなグラフ構造の構築と実行例を示します。

### 基本的な TaskGraph 構築

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
graph = TaskGraph(schedule_mode="eager")
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# 実行
graph.start_graph({s1.get_name(): [1, 2, 3]})

# サマリーを表示
summary = graph.get_graph_summary()
print(f"グラフサマリー: {summary}")

# グラフ分析
analysis = graph.get_graph_analysis()
print(f"DAG か: {analysis['isDAG']}")
print(f"レイヤー: {analysis['layersDict']}")
```

### TaskChain 線形チェーン

```python
from celestialflow import TaskChain, TaskStage

stages = [
    TaskStage("Clean", func=lambda x: x.strip().lower()),
    TaskStage("Parse", func=lambda x: int(x)),
    TaskStage("Compute", func=lambda x: x ** 2),
]

chain = TaskChain(stages, stage_mode="serial")
chain.start_chain({stages[0].get_name(): [" 10 ", " 20 ", " 30 "]})

print(f"チェーンサマリー: {chain.get_graph_summary()}")
```

### TaskCross クロスレイヤー

```python
from celestialflow import TaskCross, TaskStage

# 2層を定義
layer1 = [TaskStage("F1", func=lambda x: x * 2), TaskStage("F2", func=lambda x: x + 3)]
layer2 = [TaskStage("G1", func=lambda x: x ** 2), TaskStage("G2", func=lambda x: -x)]

cross = TaskCross(layers=[layer1, layer2], schedule_mode="eager")
cross.start_cross({layer1[0].get_name(): [1, 2], layer1[1].get_name(): [10, 20]})
print(cross.get_graph_summary())
```

### TaskGrid グリッド

```python
from celestialflow import TaskGrid, TaskStage

s00 = TaskStage("A", func=lambda x: x)
s01 = TaskStage("B", func=lambda x: x + 1)
s10 = TaskStage("C", func=lambda x: x * 2)
s11 = TaskStage("D", func=lambda x: x * x)

grid = TaskGrid(grid=[[s00, s01], [s10, s11]])
grid.start_grid({s00.get_name(): [1, 2]})
print(grid.get_graph_summary())
```

### TaskLoop リンググラフ

```python
from celestialflow import TaskLoop, TaskStage

stages = [
    TaskStage("L1", func=lambda x: x + 1),
    TaskStage("L2", func=lambda x: x * 2),
    TaskStage("L3", func=lambda x: x - 1),  # L3 -> L1 がリングを形成
]

loop = TaskLoop(stages)
# リング構造では早期終了を避けるため put_termination_signal=False を使用
loop.start_loop({stages[0].get_name(): [10]}, put_termination_signal=False)
```

### TaskWheel ホイールグラフ

```python
from celestialflow import TaskWheel, TaskStage

center = TaskStage("Center", func=lambda x: f"processed: {x}")
ring = [TaskStage(f"R{i}", func=lambda x: f"ring-{i}: {x}") for i in range(3)]

wheel = TaskWheel(center=center, ring=ring)
wheel.start_wheel({center.get_name(): ["data"]})
```

## ベストプラクティス

- 線形フローには `TaskChain` を使用 — 手動 `connect` 不要
- 多分岐並列パイプラインには `TaskCross` または手動組み合わせを使用
- 循環グラフ（`TaskLoop`/`TaskWheel`）では `put_termination_signal=False` を使用し、外部から終了を注入
- 本番環境では `set_reporter(True)` を有効にして Web 監視
- 複雑な DAG では `staged` モードを使用してレイヤーごとのデバッグを容易に
