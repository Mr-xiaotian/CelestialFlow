# 定義済みグラフ構造テスト (test_structure.py)

> 📅 最終更新日: 2026/06/05

## 目的

chain、cross、loop、wheel などの定義済みグラフ形状 helper を検証します。

## 主要ポイント

- 便利なグラフビルダーが期待通りの接続を作ることを確認します。
- トポロジ helper API の回帰を防ぎます。

## 実行方法

```bash
pytest tests/graph/test_structure.py -v
pytest tests/graph/test_structure.py -k "chain or loop or wheel" -v
```
