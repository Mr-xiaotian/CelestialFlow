# RuntimeHash

> 📅 最終更新日: 2026/05/15

`runtime/util_hash.py` はタスクハッシュとハッシュ可能変換ツールを提供します。

## 主要関数

- `make_hashable(obj)`: list/dict/set を再帰的に安定したハッシュ可能構造に変換します。
- `object_to_hash(obj)`: 任意のオブジェクトを pickle した後 SHA1 を計算し、`bytes` を返します。

## 使用例

以下の例は `make_hashable` と `object_to_hash` の使用方法を示します。

```python
from celestialflow.runtime.util_hash import make_hashable, object_to_hash

# ===== make_hashable =====
# ハッシュ不可能なオブジェクトをハッシュ可能な安定形式に変換

# リスト → 順序付きタプル
items = [3, 1, 2]
hashable_list = make_hashable(items)
print(f"リスト {items} → {hashable_list}")
print(f"ハッシュ可能: {isinstance(hashable_list, tuple)}")  # True

# ネスト辞書 → ソート済み (key, value) タプル
data = {"b": 2, "a": 1, "c": [3, 2, 1]}
hashable_dict = make_hashable(data)
print(f"辞書 {data} → {hashable_dict}")

# セット → ソート済みタプル
s = {3, 1, 2}
hashable_set = make_hashable(s)
print(f"セット {s} → {hashable_set}")

# set や dict のキーとして直接使用可能
seen = set()
seen.add(make_hashable({"name": "alice", "age": 30}))
print(f"{"alice".upper()} は処理済みか: {make_hashable({"name": "alice", "age": 30}) in seen}")  # True

# ===== object_to_hash =====
# 任意のオブジェクトの SHA1 バイト列を計算

hash_bytes = object_to_hash({"task": "process", "id": 42})
print(f"SHA1 バイト列: {hash_bytes.hex()}")
print(f"長さ: {len(hash_bytes)} bytes")  # 20 (SHA1)

# 同一内容は同一ハッシュを生成
hash_bytes_2 = object_to_hash({"task": "process", "id": 42})
print(f"一貫性: {hash_bytes == hash_bytes_2}")  # True
```

## 用途

- タスク重複排除。
- タスク識別子の生成。
