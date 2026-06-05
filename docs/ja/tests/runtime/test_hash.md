# ハッシュ utility テスト (test_hash.py)

> 📅 最終更新日: 2026/06/05

## 目的

一般的な Python 構造に対する `make_hashable` と `object_to_hash` を検証します。

## 主要ポイント

- list、dict、set、ネスト構造、型依存ハッシュを扱います。
- ハッシュ結果が安定かつ固定長であることを確認します。

## 実行方法

```bash
pytest tests/runtime/test_hash.py -v
pytest tests/runtime/test_hash.py -k "make_hashable" -v
pytest tests/runtime/test_hash.py -k "object_to_hash" -v
```
