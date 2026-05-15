# RuntimeHash

> 📅 最終更新日: 2026/05/15

`runtime/util_hash.py` はタスクハッシュとハッシュ可能変換ユーティリティを提供します。

## 主要関数

- `make_hashable(obj)`：list/dict/set を再帰的に安定したハッシュ可能な構造に変換します。
- `object_to_hash(obj)`：任意のオブジェクトを pickle してから SHA1 を計算し、`bytes` を返します。

## 用途

- タスク重複排除。
- タスク ID の生成。
