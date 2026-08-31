# graph テストパッケージ

> 📅 最終更新日: 2026/08/31

## 役割
`tests/graph/` はタスクグラフ構築、トポロジ解析、構造レンダリング、グラフレベルのスケジューリング動作、および `TaskLoop`、`TaskWheel` などの循環グラフ構造の専用テストをカバーし、主に `celestialflow.graph` モジュールに対応します。

## 含まれるテストファイル
- `test_estimators.py`: 残り時間推定と DAG 負荷伝播アルゴリズム。
- `test_graph.py`: `TaskGraph` の構築、スケジューリング、エラー収集、ライフサイクルをカバー。
- `test_order_graph.py`: `OrderGraph` 構築、ソースノード識別、階層計算、SCC 分割、深グラフリグレッションなどのグラフ解析基礎能力をカバー。
- `test_render.py`: 構造グラフを枠付きツリー型テキストリストへレンダリングする機能（従来のシリアライズテストを置き換え）をカバー。
- `test_structure.py`: `TaskLoop` と `TaskWheel` の循環グラフ構造の専用解析と入力検証をカバー。

## 実行方法

```bash
pytest tests/graph -v
pytest tests/graph -k "graph or order_graph or structure or render" -v
```
