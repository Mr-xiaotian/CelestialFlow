# 哈希工具测试 (test_hash.py)

> 📅 最后更新日期: 2026/06/05

## 作用
验证 `make_hashable` 与 `object_to_hash` 能稳定处理常见 Python 数据结构，为任务去重和 `TaskEnvelope.get_hash()` 提供基础保证。

## 覆盖点
- `make_hashable` 会把 list / dict / set / 嵌套结构递归转换为可哈希表示。
- `object_to_hash` 返回固定 20 字节的 SHA1 摘要。
- 相同结构对象的哈希应一致，不同对象的哈希应不同。

## 关键场景
- 基本类型、空容器、嵌套列表、嵌套字典、集合和混合结构。
- 同值不同对象返回相同哈希。
- 不同类型但看起来相近的值，如 `1`、`"1"`、`[1]`、`{"a": 1}`，哈希互不相同。

## 运行方式

```bash
pytest tests/runtime/test_hash.py -v
pytest tests/runtime/test_hash.py -k "make_hashable" -v
pytest tests/runtime/test_hash.py -k "object_to_hash" -v
```
