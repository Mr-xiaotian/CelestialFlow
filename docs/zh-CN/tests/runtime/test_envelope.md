# 任务信封测试 (test_envelope.py)

> 最后更新日期: 2026/06/05

## 作用
验证 `celestialflow.runtime.core_envelope` 模块中的 `TaskEnvelope` 类，确保任务数据、ID、来源和哈希值在传递过程中的完整性与一致性。

## 核心测试对象
- `TaskEnvelope`: 包装任务数据的核心容器。
- `object_to_hash`: 通用的对象哈希计算工具。

## 关键测试流程
1. **基础属性**: 验证构造函数参数（task, id, source）能否通过 Getter 方法准确还原。
2. **哈希一致性**: 
   - 验证相同内容的对象产生相同的哈希，不同内容产生不同哈希。
   - 验证哈希值固定为 20 字节（SHA1）。
3. **延迟计算**: 验证哈希值仅在首次调用 `get_hash()` 时才进行计算，优化内存和 CPU 性能。
4. **不可 hash 任务兜底**:
   - 验证任务对象无法被 pickle 时，`TaskEnvelope.get_hash()` 会返回一个当前 envelope 唯一的兜底字节串。
   - 验证该兜底值不会与其他不可 hash envelope 复用。
5. **内存效率**: 验证 `__slots__` 机制是否生效，防止在信封对象上动态添加非法属性。

## 测试重点
- **不可变性模拟**: 虽然 `TaskEnvelope` 不是严格不可变的，但通过 `__slots__` 限制了其扩展性。
- **哈希鲁棒性**: 确保 `object_to_hash` 能处理各种 Python 数据类型（字典、列表、字符串、数字）。
- **失败降级策略**: 确保不可 hash 任务不会因为哈希计算失败而中断其他任务处理流程。
- **ID 修改**: 验证 `id` 属性的可写性，用于在流转过程中重新标记任务。

## 运行方式

```bash
# 全部执行
pytest tests/runtime/test_envelope.py -v

# 仅运行哈希一致性测试
pytest tests/runtime/test_envelope.py -k "hash" -v

# 仅运行延迟计算测试
pytest tests/runtime/test_envelope.py -k "lazy" -v

# 仅运行不可 hash 任务兜底测试
pytest tests/runtime/test_envelope.py -k "unhashable" -v

# 仅运行 slots 内存测试
pytest tests/runtime/test_envelope.py -k "slots" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskEnvelope` | ~0.1s（纯内存操作） |

## 重要细节
- 哈希计算排除了 `id` 字段的影响，确保内容相同但 ID 不同的任务被识别为重复。
- 对于不可被 pickle 的任务，测试会验证 `TaskEnvelope` 返回带专用前缀的唯一兜底值，而不是把异常向上传播。
- `test_slots_memory_efficient` 使用 `pytest.raises(AttributeError)` 验证内存优化限制。

## 注意事项
- 任务信封是系统在不同节点间传递数据的统一格式。
- 相关实现位于 `src/celestialflow/runtime/core_envelope.py`。
