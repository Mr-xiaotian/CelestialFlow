# ハッシュユーティリティテスト (test_hash.py)

> 📅 最終更新日: 2026/06/05

## 役割
`make_hashable` と `object_to_hash` が一般的な Python データ構造を安定的に処理できることを検証し、タスク重複排除と `TaskEnvelope.get_hash()` の基盤保証を提供します。

## カバレッジポイント
- `make_hashable` は list / dict / set / ネスト構造を再帰的にハッシュ可能な表現に変換します。
- `object_to_hash` は固定20バイトの SHA1 ダイジェストを返します。
- 同一構造オブジェクトのハッシュは一貫し、異なるオブジェクトのハッシュは異なります。

## 主要シナリオ
- 基本型、空コンテナ、ネストリスト、ネスト辞書、セット、混合構造。
- 値が同じで異なるオブジェクトが同一ハッシュを返す。
- 型は異なるが見た目が似ている値（例：`1`、`"1"`、`[1]`、`{"a": 1}`）のハッシュが互いに異なる。

## 実行方法

```bash
pytest tests/runtime/test_hash.py -v
pytest tests/runtime/test_hash.py -k "make_hashable" -v
pytest tests/runtime/test_hash.py -k "object_to_hash" -v
```
