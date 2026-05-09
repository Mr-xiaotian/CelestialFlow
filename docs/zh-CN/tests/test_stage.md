# test_stage.py 测试说明

> 📅 最后更新日期: 2026/05/09

## 测试目标

验证 `TaskStage` 的配置层行为，包括：tag 生成与失效机制、stage_mode / execution_mode 的合法性校验。这些测试覆盖 `TaskStage` 作为图节点的元数据管理层，而非其执行能力（执行能力在 `test_executor.py` 中覆盖）。

## 测试范围

| 测试类 | 用例数 | 覆盖点 |
|--------|--------|--------|
| `TestTaskStageConfig` | 8 | tag 生成、tag 变更、stage_mode 合法值、execution_mode 合法值、非法值拦截、summary 字段 |

### 关键用例详解

#### `test_stage_tag_auto_generation`
- **目标**：未指定 tag 时，自动生成包含 `name` 和 `func_name` 的 tag。
- **格式**：`Stage[{func_name}]` 或自定义 name。

#### `test_stage_tag_changes_with_name`
- **目标**：修改 `name` 后，旧 tag 应失效，新 tag 反映新名称。
- **实现机制**：`set_name()` 通过 `delattr(self, "_tag")` 删除缓存的 tag，下次 `get_tag()` 调用时重新计算。
- **风险点**：若在多线程场景下，其他线程已缓存旧 tag 后主线程修改了 name，可能导致 tag 不一致。

#### `test_invalid_stage_mode`
- **目标**：非法 `stage_mode`（非 `"serial"` / `"thread"`）应抛出 `StageModeError`。

#### `test_invalid_execution_mode`
- **目标**：非法 `execution_mode`（非 `"serial"` / `"thread"` / `"async"`）应抛出 `ExecutionModeError`。

#### `test_summary_contains_stage_mode`
- **目标**：`get_summary()` 返回的字典应包含 `stage_mode` 和 `execution_mode` 字段，用于监控面板展示。
- **注意**：`execution_mode` 在 non-serial 模式下会附加 workers 数量，如 `"thread-20"`。

## 依赖

| 依赖 | 说明 |
|------|------|
| `pytest` | 测试框架 |
| `celestialflow.TaskStage` | 被测对象 |
| `celestialflow.runtime.util_errors` | `ExecutionModeError`、`StageModeError` |

## 可能的问题与注意事项

### 1. `get_tag()` 的线程安全性
`get_tag()` 使用 `hasattr` + 动态设属性的模式实现懒加载缓存：
```python
if hasattr(self, "_tag"):
    return str(self._tag)
self._tag = f"{self.get_name()}[{self.get_func_name()}]"
```

在多线程环境下，可能出现：
- 线程 A 检查 `hasattr` 返回 `False`
- 线程 B 同时检查也返回 `False`
- 两个线程都创建 `_tag`，虽然结果相同，但存在竞态

**建议**：若未来需要线程安全，应改用 `@functools.cached_property` 或在 `__init__` 中固化。

### 2. `test_valid_execution_mode_thread` 中未验证 `max_workers`
测试仅验证了 `execution_mode` 被设为 `"thread"`，但未验证 `max_workers` 的默认值（20）是否生效，也未测试非法值（如 0、-1）的拦截。

**建议补充**：
```python
def test_invalid_max_workers():
    with pytest.raises(ValueError):
        TaskStage(add_one, execution_mode="thread", max_workers=0)
```

## 运行方式

```bash
pytest tests/test_stage.py -v
```

所有用例均为纯配置校验，无线程启动，执行时间 `< 50ms`。

## 相关文件

- `src/celestialflow/stage/core_stage.py`：被测实现
- `src/celestialflow/stage/core_executor.py`：父类 `TaskExecutor`
- `src/celestialflow/utils/util_debug.py`：`find_unpickleable`
- `tests/test_graph.py`：在图集成场景中使用 `TaskStage`
