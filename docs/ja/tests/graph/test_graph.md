# TaskGraph テスト (test_graph.py)

> 📅 最終更新日: 2026/06/05

## 目的

ステージ登録、グラフ起動、ランタイムスナップショット、失敗収集を含む主要グラフ実行オブジェクトを検証します。

## 主要ポイント

- トポロジ構築と実行時ライフサイクルの両方を扱います。
- グラフ全体のオーケストレーションに対する高価値の回帰テストです。

## 実行方法

```bash
pytest tests/graph/test_graph.py -v
pytest tests/graph/test_graph.py -k "graph or snapshot" -v
```
