# GraphAnalysis

> 📅 最終更新日: 2026/05/28

`graph/util_analysis.py` は `networkx` ベースのグラフ分析ツールを提供します。

## 主要機能

- `build_networkx_graph(out_edges, stage_dict)`: 隣接リストと Stage マッピングから `networkx.DiGraph` を構築。
- `compute_node_levels(G)`: 有向グラフのレベル分割を実行（DAG と循環グラフの両方をサポート）。`node -> level` のマッピングを返す。
- `find_source_nodes(G)`: 有向グラフのソースノード（入次数が 0 のノード）を検出し、ソースノードリストを返す。

## 使用例

以下に、各グラフ分析関数の使用例を示します。

```python
import networkx as nx
from celestialflow import TaskGraph, TaskStage
from celestialflow.graph.util_analysis import (
    build_networkx_graph,
    compute_node_levels,
    find_source_nodes,
)

# 1. DAG を持つ TaskGraph を構築
s1 = TaskStage("A", func=lambda x: x + 1)
s2 = TaskStage("B", func=lambda x: x * 2)
s3 = TaskStage("C", func=lambda x: x - 1)
s4 = TaskStage("D", func=lambda x: x ** 2)

graph = TaskGraph()
graph.set_stages([s1, s2, s3, s4])
graph.connect([s1], [s2])
graph.connect([s1], [s3])
graph.connect([s2], [s4])
graph.connect([s3], [s4])

# 2. networkx DiGraph を構築
G = build_networkx_graph(graph.out_edges, graph.stage_dict)
print(f"ノード数: {G.number_of_nodes()}")  # 4
print(f"エッジ数: {G.number_of_edges()}")  # 4
print(f"ノード属性: {dict(G.nodes(data=True))}")

# 3. ノードレベルを計算
levels = compute_node_levels(G)
print(f"ノードレベル: {levels}")
for node, lv in sorted(levels.items(), key=lambda x: x[1]):
    print(f"  レベル {lv}: {node}")

# 4. ソースノードを検出（入次数 0）
sources = find_source_nodes(G)
print(f"ソースノード: {sources}")  # ['A']
```

### TaskGraph.get_graph_analysis との統合

```python
from celestialflow import TaskGraph, TaskStage

# グラフを構築し、実行後に分析情報を取得
graph = TaskGraph()
s1 = TaskStage("X", func=lambda x: x)
s2 = TaskStage("Y", func=lambda x: x * 2)
graph.set_stages([s1, s2])
graph.connect([s1], [s2])

analysis = graph.get_graph_analysis()
print(f"DAG かどうか: {analysis['isDAG']}")  # True
print(f"スケジュールモード: {analysis['scheduleMode']}")  # eager
print(f"レイヤー分布: {analysis['layersDict']}")
print(f"隣接リスト: {analysis['out_edges']}")

# networkx グラフを取得
nx_graph = graph.get_networkx_graph()
print(f"型: {type(nx_graph).__name__}")  # DiGraph
```

## 使用シーン

- TaskGraph 初期化後の DAG 判定分析。
- staged スケジューリングに必要なレイヤー情報の生成。
- タスク注入用のソースノードの自動識別。
- トポロジー可視化のためのレベルデータ提供。
