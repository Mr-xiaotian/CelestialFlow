# 哈希工具测试 (test_hash.py)

> 📅 最后更新日期: 2026/05/28

## 作用

验证 `celestialflow.runtime.util_hash` 中的 `make_hashable` 和 `object_to_hash` 两个哈希工具函数，确保任意 Python 对象都能被稳定地转换为可哈希形式并生成唯一摘要。

## 核心测试对象

- `make_hashable`: 递归地将列表、字典、集合等不可哈希对象转换为可哈希结构（元组）。
- `object_to_hash`: 对任意对象计算 20 字节 SHA1 摘要，用于任务去重。

## 关键测试场景

### `make_hashable`
- **基本类型原样返回**：`int`、`str`、`float`、`bool`、`None` 不变
- **元组原样返回**：本身即哈希，无需转换
- **空容器**：`[]` → `()`，`{}` → `()`
- **列表转元组**：`[1, 2, 3]` → `(1, 2, 3)`
- **嵌套列表**：`[[1, 2], [3, 4]]` → `((1, 2), (3, 4))`
- **字典**：转为排序后的 `(key, value)` 元组对，保证确定性
- **嵌套字典**：递归转换内部值
- **混合类型**：列表中包含字典和基本类型
- **集合**：转为排序后的元组
- **结果可哈希**：转换结果可作为 `set` 元素 / `dict` key

### `object_to_hash`
- **返回类型**：20 字节 `bytes`
- **幂等性**：同一对象多次调用产生相同哈希
- **同构同哈希**：相同结构的对象产生相同哈希
- **异值异哈希**：`1`、`"1"`、`[1]`、`{"a": 1}` 互不相同
- **嵌套结构**：复杂嵌套对象正确计算
- **空容器区分**：`[]`、`{}`、`()` 三种空容器产生不同哈希

## 运行方式

```bash
# 全部执行
pytest tests/utils/test_hash.py -v

# 仅运行 make_hashable 测试
pytest tests/utils/test_hash.py -k "make_hashable" -v

# 仅运行 object_to_hash 测试
pytest tests/utils/test_hash.py -k "object_to_hash" -v

# 仅运行嵌套结构测试
pytest tests/utils/test_hash.py -k "nested" -v
```

## 性能参考

| 测试类 | 耗时 |
|--------|------|
| `TestUtilHash` | ~0.05s |

## 重要细节

- `make_hashable` 对字典和集合按 key 排序后转换，确保 `{"b": 2, "a": 1}` 和 `{"a": 1, "b": 2}` 产生相同结果。
- `object_to_hash` 内部调用 `make_hashable` 再经由 `pickle` 序列化后计算 SHA1。
- 两种哈希均用于框架的去重机制：`make_hashable` 用于内存内快速对比，`object_to_hash` 用于持久化 / 跨进程对比。

## 注意事项

- 哈希工具是任务去重功能的基础，错误实现会导致重复任务漏检或误判。
- 相关实现位于 `src/celestialflow/runtime/util_hash.py`。
