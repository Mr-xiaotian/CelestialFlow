# グラフ解析テスト (test_analysis.py)

> 📅 最終更新日: 2026/06/05

## 目的

ソースノード検出、ノードレベル計算、解析用グラフメタデータ生成 helper を検証します。

## 主要ポイント

- タスク実行ではなくグラフ形状の推論に焦点を当てます。
- DAG と依存関係解析の安定性を保ちます。

## 実行方法

```bash
pytest tests/graph/test_analysis.py -v
pytest tests/graph/test_analysis.py -k "source or level" -v
```
