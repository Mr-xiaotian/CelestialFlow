# 运行时类型测试 (test_types.py)

> 📅 最后更新日期: 2026/05/28

## 作用

验证 `celestialflow.runtime.util_types` 中所有运行时辅助类型的正确性，包括终止信号、计数器、上下文管理器、事件常量和错误记录。

## 核心测试对象

| 类型 | 说明 |
|------|------|
| `TerminationSignal` | 终止信号，携带 `id` 和 `source` |
| `TerminationIdPool` | 多终止信号 ID 池，用于合并传播 |
| `NoOpContext` | 空上下文管理器，无锁场景的占位实现 |
| `ValueWrapper` | 带锁的值包装器，支持线程安全读写 |
| `SumCounter` | 多计数器聚合累加器，支持 `init_value` 和重置 |
| `StageStatus` | Stage 生命周期枚举（NOT_STARTED / RUNNING / STOPPED） |
| `CTreeEvent` | CTree 事件名常量 |
| `PersistedErrorRecord` | 持久化错误记录（frozen dataclass） |

## 关键测试场景

### `TerminationSignal`
- 默认构造：`id=-1`, `source="input"`
- 自定义参数：`_id=42`, `source="queue"`
- 部分参数跳过

### `TerminationIdPool`
- 非空列表、空列表、单元素列表构造

### `NoOpContext`
- `with` 语句正常进出，变量状态保留
- 异常不被抑制（`__exit__` 返回 `None`）
- 直接调用 `__enter__` / `__exit__`

### `ValueWrapper`
- 基本读写：`value` 属性正常存取
- 默认值为 0
- 带锁读写行为一致
- `get_lock()` 返回传入的 `Lock` 或 `NoOpContext`
- 负数值边界

### `SumCounter`
- 单计数器 / 多计数器累加
- `init_value` 影响总和
- `reset()` 清零所有计数器（包括 `init_value`）
- 空计数器：`value=0`
- `thread` mode 模式正常累加

### `StageStatus`
- 枚举值正确（0 / 1 / 2）
- `IntEnum` 可与整数比较
- 成员数量为 3

### `CTreeEvent`
- 任务常量正确（`task.input`, `task.success`, `task.error`, `task.duplicate`）
- 终止常量正确（`termination.input`, `termination.merge`）
- 重试前缀以 `"."` 结尾

### `PersistedErrorRecord`
- 基本 / 全字段构造
- Frozen dataclass 不可修改
- `__str__` 返回 `error_repr`
- `get_group_key()` 返回 `(error_type, error_message)` 元组

## 运行方式

```bash
# 全部执行
pytest tests/utils/test_types.py -v

# 仅运行终止信号测试
pytest tests/utils/test_types.py -k "termination" -v

# 仅运行计数器测试
pytest tests/utils/test_types.py -k "counter or Sum or Value" -v

# 仅运行枚举和事件测试
pytest tests/utils/test_types.py -k "status or event or Stage or CTree" -v

# 仅运行错误记录测试
pytest tests/utils/test_types.py -k "error" -v
```

## 性能参考

| 测试类 | 耗时 |
|--------|------|
| `TestUtilTypes` | ~0.1s |

## 重要细节

- `NoOpContext` 是 Null Object 模式实现，用于无锁场景下 `ValueWrapper.get_lock()` 的统一接口。
- `ValueWrapper` 的 `get_lock()` 返回上下文管理器（`Lock` 或 `NoOpContext`），调用方统一使用 `with` 语句。
- `PersistedErrorRecord` 是 frozen dataclass，确保错误记录在持久化后不可篡改。
- `StageStatus` 是 `IntEnum`，可直接与整数比较（如 `status > StageStatus.NOT_STARTED`）。

## 注意事项

- 这些类型被框架核心代码广泛使用，正确性直接影响调度、去重、报告等关键链路。
- 相关实现位于 `src/celestialflow/runtime/util_types.py`。
