# RuntimeHash

`runtime/util_hash.py` 提供任务哈希与可哈希转换工具。

## 主要函数

- `make_hashable(obj)`：把 list/dict/set 递归转换为稳定可哈希结构。
- `object_to_str_hash(obj)`：对任意对象做 pickle 后计算 SHA1。

## 用途

- Task 去重。
- 任务身份标识生成。
