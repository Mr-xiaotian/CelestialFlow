# graph テストパッケージ

> 📅 最終更新日: 2026/06/05

## 目的

グラフ解析 helper、`TaskGraph`、構造シリアライズのテストをまとめます。

## 主要ポイント

- ソースノード検出とグラフ実行挙動を検証します。
- JSON / テキスト構造レンダリング helper も含みます。

## 実行方法

```bash
pytest tests/graph -v
pytest tests/graph -k "graph or analysis" -v
```
