# 任务信封测试 (test_envelope.py)

> 最后更新日期: 2026/06/11

## 作用
验证 `celestialflow.runtime.core_envelope` 模块中的 `TaskEnvelope` 类及 `object_to_hash` 哈希工具，确保任务数据、ID、来源和哈希值在传递过程中的完整性与一致性。

## 核心测试对象
- `TaskEnvelope`: 包装任务数据的核心容器。
- `object_to_hash`: 通用的对象哈希计算工具。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestTaskEnvelope` | 8 | 构造函数/Getter、source 保留、ID 修改、哈希一致性、延迟计算、不可 hash 兜底、`__slots__` 内存限制 |
| `TestObjectToHash` | 4 | 返回类型(bytes)、SHA1 定长 20 字节、相同输入一致、不同输入不同 |

## 关键测试场景

### `TestTaskEnvelope`
1. **基础属性**: 验证构造函数参数（task, id, source）能否通过 Getter 方法准确还原。
2. **哈希一致性**:
   - 验证相同内容的对象产生相同的哈希（即便 ID 不同）。
   - 验证不同内容产生不同哈希。
3. **延迟计算**: 验证哈希值仅在首次调用 `get_hash()` 时才进行计算，初始 `hash` 属性为 `None`。
4. **不可 hash 任务兜底**:
   - 验证任务对象无法被 pickle 时，`get_hash()` 会返回一个以 `__unhashable_task__:` 为前缀的唯一兜底字节串。
   - 验证两个不同的不可 hash 任务不会复用同一兜底值。
5. **内存效率**: 验证 `__slots__` 机制生效，动态添加属性时抛出 `AttributeError`。

### `TestObjectToHash`
- 验证返回值固定为 20 字节的 SHA1 摘要。
- 验证相同结构对象在不同调用中产生一致哈希。
- 验证不同对象产生不同哈希。

## 测试重点
- **不可变性模拟**: 虽然 `TaskEnvelope` 不是严格不可变的，但通过 `__slots__` 限制了其扩展性。
- **哈希鲁棒性**: 确保 `object_to_hash` 能处理各种 Python 数据类型。
- **失败降级策略**: 确保不可 hash 任务不会因为哈希计算失败而中断其他任务处理流程。
- **ID 修改**: 验证 `id` 属性的可写性（`envelope.id = 999`），用于在流转过程中重新标记任务。

## 运行方式

```bash
# 全部执行
pytest tests/runtime/test_envelope.py -v

# 仅运行信封属性测试
pytest tests/runtime/test_envelope.py -k "Envelope" -v

# 仅运行 object_to_hash 测试
pytest tests/runtime/test_envelope.py -k "ObjectToHash" -v

# 仅运行哈希一致性测试
pytest tests/runtime/test_envelope.py -k "hash" -v

# 仅运行不可 hash 任务兜底测试
pytest tests/runtime/test_envelope.py -k "unhashable" -v

# 仅运行 slots 内存测试
pytest tests/runtime/test_envelope.py -k "slots" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskEnvelope` | ~0.1s（纯内存操作） |
| `TestObjectToHash` | < 0.1s（纯内存操作） |

## 重要细节
- 哈希计算排除了 `id` 字段的影响，确保内容相同但 ID 不同的任务被识别为重复。
- 对于不可被 pickle 的任务，测试会验证返回带专用前缀的唯一兜底值，而不是把异常向上传播。
- `test_slots_memory_efficient` 使用 `pytest.raises(AttributeError)` 验证内存优化限制。

## 注意事项
- 任务信封是系统在不同节点间传递数据的统一格式。
- 相关实现位于 `src/celestialflow/runtime/core_envelope.py`。
