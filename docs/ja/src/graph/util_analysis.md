# GraphAnalysis

> 📅 最終更新日: 2026/05/15

`graph/util_analysis.py` は `networkx` ベースのグラフ分析ツールを提供します。

## 主要機能

- `build_networkx_graph(out_edges, stage_runtime_dict)`: 隣接リストとステージランタイム情報から `networkx.DiGraph` を構築。
- `compute_node_levels(G)`: 有向グラフのレベル分割を実行（DAG と循環グラフの両方をサポート）。`node -> level` のマッピングを返す。
- `find_source_nodes(G)`: 有向グラフのソースノード（入次数が 0 のノード）を検出し、ソースノードリストを返す。

## 使用シーン

- TaskGraph 初期化後の DAG 判定分析。
- staged スケジューリングに必要なレイヤー情報の生成。
- タスク注入用のソースノードの自動識別。
- トポロジー可視化のためのレベルデータ提供。
