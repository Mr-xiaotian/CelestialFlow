# GraphAnalysis

`graph/util_analysis.py` は `networkx` に基づくグラフ分析ツールを提供します。

## 主な機能

- `format_networkx_graph(structure_graph)`: シリアライズされた構造 JSON を `networkx.DiGraph` に変換します。
- `compute_node_levels(G)`: DAG に対してレベル分割を行い、`node -> level` のマッピングを返します。

## 使用シーン

- TaskGraph の初期化後にグラフが DAG であるかどうかを分析します。
- staged スケジューリングに必要なレイヤー情報を生成します。
- トポロジカル可視化のためのレベルデータを提供します。
