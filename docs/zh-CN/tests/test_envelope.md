# test_envelope.py 测试说明

> 📅 最后更新日期: 2026/05/15

## 测试目标

验证 `TaskEnvelope` 任务信封的核心行为，包括构造、getter 方法、惰性哈希、属性持久化、哈希一致性以及内存优化机制。`TaskEnvelope` 是 CelestialFlow 中任务在队列间传递的基本单元，其正确性直接影响整个数据流的可靠性。

## 测试范围

| 测试类 | 用例数 | 覆盖点 |
|--------|--------|--------|
| `TestTaskEnvelope` | 7 | 构造与 getter、source、change_id、不同哈希、相同哈希、惰性哈希、slots |
| `TestObjectToHash` | 4 | 返回 bytes 类型、SHA1 长度、相同输入相同哈希、不同输入不同哈希 |

### 详细用例说明

#### `test_create_and_getters`
- **目标**：验证构造函数和 getter 方法能正确创建和读取信封数据。
- **输入**：`{"key": "value", "num": 42}`，`id=100`
- **断言**：`get_task()` 返回原始数据；`get_id()` 返回 100；`get_hash()` 返回 `bytes` 类型且长度大于 0。

#### `test_source_preserved`
- **目标**：验证 `source` 属性在构造过程中不丢失。
- **背景**：`source` 用于追溯任务来源（如 `"input"`、上游 stage 的 tag）。

#### `test_change_id`
- **目标**：验证 `change_id()` 能修改信封 ID（用于重试场景生成新的追踪 ID）。

#### `test_different_tasks_different_hash`
- **目标**：验证不同 payload 产生不同的 `hash` 值。

#### `test_same_task_same_hash`
- **目标**：验证相同 payload 产生相同的 `hash` 值。
- **用途**：去重检查（`enable_duplicate_check=True`）依赖此特性。

#### `test_lazy_hash`
- **目标**：验证 `hash` 在构造时为 `None`，首次调用 `get_hash()` 时才计算。
- **断言**：构造后 `envelope.hash is None`；调用 `get_hash()` 后 `envelope.hash is not None`。

#### `test_slots_memory_efficient`
- **目标**：验证 `__slots__` 生效，阻止动态属性添加。

## 依赖

| 依赖 | 说明 |
|------|------|
| `pytest` | 测试框架 |
| `celestialflow.runtime.core_envelope.TaskEnvelope` | 被测对象 |
| `celestialflow.runtime.util_hash.object_to_hash` | 哈希工具函数 |

### `TestObjectToHash` 详细用例说明

#### `test_returns_bytes`
- **目标**：验证 `object_to_hash()` 返回 `bytes` 类型。

#### `test_returns_20_bytes`
- **目标**：验证 SHA1 digest 的长度为 20 字节。

#### `test_same_input_same_hash`
- **目标**：验证相同输入产生相同哈希值。

#### `test_different_input_different_hash`
- **目标**：验证不同输入产生不同哈希值。

## 运行方式

```bash
pytest tests/test_envelope.py -v
```

## 相关文件

- `src/celestialflow/runtime/core_envelope.py`：被测实现
- `src/celestialflow/runtime/util_hash.py`：hash 计算逻辑
- `tests/test_queue.py`：使用 `TaskEnvelope` 进行队列操作测试
