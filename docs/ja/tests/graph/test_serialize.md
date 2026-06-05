# グラフシリアライズテスト (test_serialize.py)

> 📅 最終更新日: 2026/06/05

## 目的

グラフ構造を JSON 風データと整形ツリー出力へ変換する helper を検証します。

## 主要ポイント

- Web UI 用の構造グラフ生成を確認します。
- テキスト表現と構造表現の整合性を保ちます。

## 実行方法

```bash
pytest tests/graph/test_serialize.py -v
pytest tests/graph/test_serialize.py -k "structure or serialize" -v
```
