# JSONL 工具测试 (test_jsonl.py)

> 最后更新日期: 2026/05/23

## 作用
验证 `celestialflow.persistence.util_jsonl` 中的工具函数，确保能准确解析、过滤和分组基于 JSONL 格式的持久化日志。

## 核心测试对象
- `parse_jsonl_value`: 智能解析字符串值为 Python 原生类型（数字、布尔、元组等）。
- `load_jsonl_logs`: 批量加载并过滤日志行。
- `load_jsonl_by_key`: 按单个键（如 stage）分组提取字段。
- `load_jsonl_grouped_by_keys`: 按多个键的组合进行分组。
- `load_task_error_pairs`: 专门用于提取任务与错误记录的配对。

## 关键测试流程
1. **智能解析**: 验证字符串 "1" 转为整数，"True" 转为布尔值，"[1, 2]" 转为元组。
2. **错误字符串拆分**: 验证从 `ValueError(msg)` 格式中提取错误类型和消息内容。
3. **结构化读取**: 模拟包含 Meta 行、普通数据行和复杂任务行（如元组 ID）的 JSONL 文件，验证读取的完整性。
4. **多级分组**: 验证按 `(error, stage)` 组合键进行分组的逻辑。

## 测试重点
- **鲁棒性**: 确保 Meta 行或格式不一致的行在读取时被正确跳过。
- **类型还原**: 验证从 JSONL 恢复出的任务数据能保持原始类型（如 `(1, 2)` 元组）。
- **字段过滤**: 验证 `keys` 参数能有效减少内存占用，仅提取需要的字段。

## 运行方式

```bash
# 全部执行
pytest tests/persistence/test_jsonl.py -v

# 仅运行智能解析测试
pytest tests/persistence/test_jsonl.py -k "parse" -v

# 仅运行分组读取测试
pytest tests/persistence/test_jsonl.py -k "group" -v

# 仅运行错误配对测试
pytest tests/persistence/test_jsonl.py -k "error_pair" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestJsonlUtils` | ~0.1s（纯逻辑，无 I/O 等待） |

## 重要细节
- 使用 `pytest.fixture` 创建临时的 `sample_jsonl` 文件进行测试。
- `test_load_task_error_pairs` 验证了 `PersistedErrorRecord` 数据模型的封装。

## 注意事项
- 测试代码位于 `tests/persistence/test_jsonl.py`。
