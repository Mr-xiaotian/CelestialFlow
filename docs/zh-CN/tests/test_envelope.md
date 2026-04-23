# test_envelope.py 测试说明

> 📅 最后更新日期: 2026/04/22

## 测试目标

验证 `TaskEnvelope` 任务信封的核心行为，包括数据包装/解包、属性持久化、哈希一致性以及内存优化机制。`TaskEnvelope` 是 CelestialFlow 中任务在队列间传递的基本单元，其正确性直接影响整个数据流的可靠性。

## 测试范围

| 测试类 | 用例数 | 覆盖点 |
|--------|--------|--------|
| `TestTaskEnvelope` | 6 | wrap/unwrap、source、change_id、hash、slots |

### 详细用例说明

#### `test_wrap_unwrap`
- **目标**：验证 `TaskEnvelope.wrap()` 能正确包装任意 Python 对象，且 `unwrap()` 可完整还原。
- **输入**：`{"key": "value", "num": 42}`，`task_id=100`
- **断言**：解包后的 task、hash、id 均与原始值一致；hash 为非空字符串。

#### `test_wrap_preserves_source`
- **目标**：验证 `source` 属性在包装过程中不丢失。
- **背景**：`source` 用于追溯任务来源（如 `"input"`、上游 stage 的 tag）。

#### `test_change_id`
- **目标**：验证 `change_id()` 能修改信封 ID（用于重试场景生成新的追踪 ID）。
- **注意**：修改后旧 ID 不再保留，调用方需自行维护父子关系。

#### `test_different_tasks_different_hash`
- **目标**：验证不同 payload 产生不同的 `hash` 值。
- **机制**：底层使用 `object_to_str_hash`，基于对象的规范化字符串表示计算。

#### `test_same_task_same_hash`
- **目标**：验证相同 payload 产生相同的 `hash` 值。
- **用途**：去重检查（`enable_duplicate_check=True`）依赖此特性。

#### `test_slots_memory_efficient`
- **目标**：验证 `__slots__` 生效，阻止动态属性添加。
- **收益**：每个 `TaskEnvelope` 实例节省约 50% 内存（无 `__dict__`）。

## 依赖

| 依赖 | 说明 |
|------|------|
| `pytest` | 测试框架 |
| `celestialflow.runtime.core_envelope.TaskEnvelope` | 被测对象 |

## 可能的问题与注意事项

### 1. Hash 冲突
`object_to_str_hash` 基于字符串表示计算，以下情况可能产生意外相同的 hash：
- `1` 和 `"1"`（数值与字符串）
- 不同类但 `__repr__` 输出相同的对象

**建议**：在生产环境中使用 `enable_duplicate_check` 时，确保输入任务的类型一致性。

### 2. 不可序列化对象的包装
`TaskEnvelope.wrap()` 内部会调用 `object_to_str_hash`，如果 task 包含不可序列化对象（如文件句柄、lambda），可能在 hash 计算阶段就失败。

**排查方式**：
```python
from celestialflow.runtime.util_hash import object_to_str_hash
try:
    object_to_str_hash(your_task)
except Exception as e:
    print(f"无法计算 hash: {e}")
```

### 3. `change_id` 无校验
`change_id(new_id)` 不检查 ID 唯一性，也不维护历史 ID 链。如果在重试逻辑中误用，可能导致追踪树断链。

### 4. `__slots__` 与继承限制
如果未来需要为 `TaskEnvelope` 添加子类，子类也必须声明 `__slots__`，否则会失去内存优化收益。

## 运行方式

```bash
pytest tests/test_envelope.py -v
```

## 相关文件

- `src/celestialflow/runtime/core_envelope.py`：被测实现
- `src/celestialflow/runtime/util_hash.py`：hash 计算逻辑
- `tests/test_queue.py`：使用 `TaskEnvelope` 进行队列操作测试
- `tests/test_metrics.py`：通过 hash 进行去重测试
