# tests/runtime/test_envelope.py

> 📅 最后更新日期: 2026/09/24

## 作用
验证 `celestialflow.runtime.core_envelope` 模块中的 `TaskEnvelope` 类，确保任务数据与 ID 能被信封正确保存并通过 Getter 还原，同时验证 `__slots__` 的内存约束生效。

## 核心测试对象
- `TaskEnvelope`: 包装任务数据与任务 ID 的核心容器，使用 `__slots__ = ("_id", "_task")` 限制实例属性。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestTaskEnvelope` | 3 | 构造函数/Getter、`get_id` 查询、`__slots__` 内存限制 |

## 关键测试场景

### `TestTaskEnvelope`
1. **构造与还原** (`test_create_and_getters`): 以字典任务 `{"key": "value", "num": 42}` 与 `id=100` 构造信封，验证 `get_task()` 返回原任务、`get_id()` 返回 100。
2. **ID 查询** (`test_get_id`): 以字符串任务 `"hello"` 与 `id=1` 构造，验证 `get_id()` 返回 1。
3. **内存效率** (`test_slots_memory_efficient`): 验证 `__slots__` 机制生效，为实例动态添加 `extra_attr` 时抛出 `AttributeError`。

## 测试重点
- **数据完整性**: 信封必须无损保存任务对象与 ID。
- **不可扩展性**: 通过 `__slots__` 阻止动态属性，保证内存占用可控。

## 运行方式

```bash
# 全部执行
pytest tests/runtime/test_envelope.py -v

# 仅运行 Getter 相关测试
pytest tests/runtime/test_envelope.py -k "get_id or getters" -v

# 仅运行 slots 内存测试
pytest tests/runtime/test_envelope.py -k "slots" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskEnvelope` | < 0.1s（纯内存操作） |

## 重要细节
- `test_create_and_getters` 使用非标量（字典）任务，验证信封对任意对象类型均可原样保存。
- `test_slots_memory_efficient` 使用 `pytest.raises(AttributeError)` 验证内存优化限制。

## 注意事项
- 任务信封是系统在不同节点间传递数据的统一格式。
- 相关实现位于 `src/celestialflow/runtime/core_envelope.py`。
