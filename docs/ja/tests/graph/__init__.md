# graph テストパッケージ

> 📅 最終更新日: 2026/06/11

## 役割
`tests/graph/` はタスクグラフの構築、トポロジ解析、構造エクスポート、グラフレベルスケジューリング動作、および `TaskLoop`、`TaskWheel` などの循環グラフ構造の専用テストをカバーし、主に `celestialflow.graph` モジュールに対応します。

## 含まれるテストファイル
- `test_analysis.py`: ソースノード識別、階層計算、networkx グラフ解析ヘルパー関数をカバー。
- `test_graph.py`: `TaskGraph` の構築、スケジューリング、エラー収集、ライフサイクルをカバー。
- `test_serialize.py`: 構造グラフの JSON / テキストエクスポートロジックをカバー。
- `test_structure.py`: `TaskLoop` と `TaskWheel` の循環グラフ構造専用解析をカバー。

## 実行方法

```bash
pytest tests/graph -v
pytest tests/graph -k "graph or analysis or structure" -v
```
