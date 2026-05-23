# RuntimeHash

> 📅 最后更新日期: 2026/05/15

`runtime/util_hash.py` 提供任务哈希与可哈希转换工具。

## 主要函数

- `make_hashable(obj)`：把 list/dict/set 递归转换为稳定可哈希结构。
- `object_to_hash(obj)`：对任意对象做 pickle 后计算 SHA1，返回 `bytes`。

## 使用示例

以下示例展示 `make_hashable` 和 `object_to_hash` 的用法。

```python
from celestialflow.runtime.util_hash import make_hashable, object_to_hash

# ===== make_hashable =====
# 将不可哈希的对象转换为可哈希的稳定形式

# 列表 → 有序元组
items = [3, 1, 2]
hashable_list = make_hashable(items)
print(f"列表 {items} → {hashable_list}")
print(f"可哈希: {isinstance(hashable_list, tuple)}")  # True

# 嵌套字典 → 排序后的 (key, value) 元组
data = {"b": 2, "a": 1, "c": [3, 2, 1]}
hashable_dict = make_hashable(data)
print(f"字典 {data} → {hashable_dict}")

# 集合 → 排序后的元组
s = {3, 1, 2}
hashable_set = make_hashable(s)
print(f"集合 {s} → {hashable_set}")

# 可以直接用于 set 或 dict 的 key
seen = set()
seen.add(make_hashable({"name": "alice", "age": 30}))
print(f"{"alice".upper()} 是否已处理: {make_hashable({"name": "alice", "age": 30}) in seen}")  # True

# ===== object_to_hash =====
# 对任意对象计算 SHA1 字节串

hash_bytes = object_to_hash({"task": "process", "id": 42})
print(f"SHA1 字节串: {hash_bytes.hex()}")
print(f"长度: {len(hash_bytes)} bytes")  # 20 (SHA1)

# 相同内容生成相同哈希
hash_bytes_2 = object_to_hash({"task": "process", "id": 42})
print(f"一致性: {hash_bytes == hash_bytes_2}")  # True
```

## 用途

- Task 去重。
- 任务身份标识生成。
