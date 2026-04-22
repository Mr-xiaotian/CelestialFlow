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

## 基准结果（实测）

> 环境：Windows，Python 3.10，timeit repeat=7, number=10,000

### 综合排名（所有数据类型平均）

| 方法 | 平均耗时 | 特点 |
|------|----------|------|
| `fast_mixed` | ~2.5 us | 基础类型走捷径，综合最快 |
| `pickle+blake2b16` | ~3.0 us | pickle 序列化 + 快速哈希 |
| `pickle+sha1` | ~3.2 us | 稳定、兼容性好 |
| `repr+blake2b16` | ~15 us | repr 规范化 + 快速哈希 |
| `json+md5` / `json+sha256` | ~25 us | 跨语言稳定，但最慢 |
| `repr+sha1+uuid` | ~25 us | UUID 格式输出，有额外转换开销 |

### 典型数据点（单位：微秒/次）

| Case | best | worst | 最佳方法 |
|------|------|-------|----------|
| int | ~1.3 | ~4.3 | pickle+sha1 / fast_mixed |
| short_str | ~1.3 | ~4.2 | repr+blake2b16 / fast_mixed |
| long_str_4k | ~4.1 | ~23.5 | pickle+sha1 / fast_mixed |
| bytes_4k | ~3.6 | ~58.4 | **fast_mixed**（原生支持 bytes） |
| small_dict | ~1.9 | ~17.4 | pickle+blake2b16 |
| dict_100_pairs | ~7.8 | ~104.4 | pickle+sha1 / fast_mixed |
| list_100_ints | ~2.9 | ~36.0 | fast_mixed |
| set_100_ints | ~3.7 | ~43.1 | pickle+blake2b16 / fast_mixed |

**关键结论**：
- `fast_mixed` 在 bytes 和大集合上具有绝对优势（直接哈希原始字节，避免序列化）
- `json+sha256` 和 `repr+sha1+uuid` 在所有场景下均显著慢于 pickle 方案，仅在对稳定性/格式有强需求时使用
- pickle 系列方法在小对象上表现优异（1-3 us），但注意 pickle 的跨会话稳定性风险

## 运行方式

```bash
python bench/bench_hash.py
```

## 依赖

- `celestialflow.format_table`
