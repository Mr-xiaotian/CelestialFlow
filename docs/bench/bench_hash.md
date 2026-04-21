# bench_hash.py 基准测试说明

## 目标

系统性对比 9 种对象→哈希字符串的序列化+哈希策略，为 `TaskEnvelope` 的去重和追踪 ID 生成选择最优方案。评估维度包括：速度、稳定性、碰撞率、对不同数据类型的支持度。

## 测试策略

| 方法 | 序列化方式 | 哈希算法 | 特点 |
|------|-----------|----------|------|
| `pickle+md5` | `pickle.dumps` | MD5 | 支持任意对象，但非稳定（协议版本敏感） |
| `pickle+sha1` | `pickle.dumps` | SHA1 | 同上，更长摘要 |
| `pickle+blake2b16` | `pickle.dumps` | BLAKE2b(16B) | 更快，短摘要 |
| `json+md5` | 自定义 JSON | MD5 | 跨语言稳定，但仅支持 JSON 可序列化类型 |
| `json+sha256` | 自定义 JSON | SHA256 | 更安全，但更慢 |
| `repr+md5` | `repr(normalized)` | MD5 | 可读性好，但 `set`/`dict` 顺序敏感 |
| `repr+sha1+uuid` | `repr(normalized)` | SHA1→UUID | 格式化为标准 UUID |
| `repr+blake2b16` | `repr(normalized)` | BLAKE2b(16B) | 快速 + 短摘要 |
| `fast_mixed` | 类型分支（bytes/str/repr/pickle） | SHA1 | 对基础类型走捷径，对复杂对象回退 pickle |

## 测试数据集

覆盖 11 种典型数据形态：`int`、`short_str`、`long_str_4k`、`bytes_4k`、`small_tuple`、`small_list`、`list_100_ints`、`small_dict`、`dict_100_pairs`、`nested_dict`、`set_100_ints`。

## 关键实现

- `normalize_for_hash`：将 `set`、`dict`、`tuple`、`list`、`bytes` 转为稳定结构（排序键、标记类型）
- `benchmark_one`：使用 `timeit.repeat`（7 次重复，每次 10,000 次调用），禁用 GC，输出均值和标准差

## 可能出现的问题

1. **pickle 的不稳定性**：同一对象在不同 Python 版本或不同运行中，`pickle.dumps` 的字节可能不同（尤其是集合顺序），导致 hash 不一致。**不适合跨会话去重**。
2. **`fast_mixed` 的类型分支盲区**：若传入自定义类且未实现 `__repr__`，会回退到 `pickle.dumps`，此时又面临 pickle 的不稳定性问题。
3. **UUID 格式碰撞**：`repr+sha1+uuid` 截断 SHA1 为 16 字节后转 UUID，虽概率极低，但严格来说损失了密码学安全性。
4. **大对象内存压力**：`long_str_4k`、`bytes_4k` 在 10,000 次重复测试中可能短暂占用大量内存。

## 运行方式

```bash
python bench/bench_hash.py
```

## 依赖

- `celestialflow.format_table`
