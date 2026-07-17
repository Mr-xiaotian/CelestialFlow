# ハッシュユーティリティテスト (test_hash.py)

> 📅 最終更新日: 2026/07/16

## 役割
`make_hashable` と `object_to_hash` が一般的な Python データ構造を安定的に処理できることを検証し、タスク重複排除と `TaskEnvelope.get_hash()` の基盤保証を提供します。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|--------|--------|---------|
| `TestUtilHash` | 19 | `make_hashable` 基本型/空コンテナ/リスト/タプル/辞書/セット/ネスト/混合構造の再帰変換とハッシュ可能検証；`object_to_hash` 戻り値型/SHA1 20バイト/冪等性/異なるオブジェクトで異なるハッシュ/ネスト構造/空コンテナ区別/呼び出し間一貫性 |

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
