# RuntimeHash

`runtime/util_hash.py` はタスクのハッシュ計算とハッシュ可能変換ユーティリティを提供します。

## 主要関数

- `make_hashable(obj)`: list/dict/set を安定したハッシュ可能な構造に再帰的に変換します。
- `object_to_str_hash(obj)`: 任意のオブジェクトを pickle した後、SHA1 ハッシュを計算します。

## 用途

- タスクの重複排除。
- タスクのアイデンティティ生成。
