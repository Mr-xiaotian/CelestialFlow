# 自定义异常类测试 (test_errors.py)

> 📅 最后更新日期: 2026/05/28

## 作用

验证 `celestialflow.runtime.util_errors` 中所有自定义异常类的实例化、继承关系和信息完整性，确保框架各模块能正确抛出和捕获预期类型的异常。

## 核心测试对象

所有自定义异常类，按功能分为四组：

| 分组 | 异常类 | 说明 |
|------|--------|------|
| 基础 | `CelestialFlowError` | 框架所有异常的基类 |
| 配置与选项 | `ConfigurationError`, `InvalidOptionError`, `ExecutionModeError`, `StageModeError`, `LogLevelError`, `ScheduleModeError` | 参数校验与模式配置错误 |
| 图结构 | `GraphStructureError`, `DuplicateNodeError`, `UnknownNodeError` | DAG 拓扑与节点校验错误 |
| 运行时与外部 | `RuntimeStateError`, `InitializationError`, `CelestialFlowTimeoutError`, `UnconsumedError`, `RemoteWorkerError`, `ReporterError`, `CelestialTreeConnectionError`, `TaskFormatError`, `TerminationMergeError` | 生命周期、外部服务及任务逻辑错误 |

## 关键测试场景

- **基类实例化**：`CelestialFlowError("something went wrong")` 是 `Exception` 子类
- **继承链验证**：`ExecutionModeError` 同时是 `CelestialFlowError` 和 `InvalidOptionError` 的实例
- **字段完整性**：`InvalidOptionError` 的 `field`、`value`、`allowed` 属性正确填充
- **有效值列举**：`ExecutionModeError`、`StageModeError`、`LogLevelError` 等的 `valid_modes` / `valid_levels` 包含正确枚举
- **默认消息**：`CelestialTreeConnectionError()` 无参构造时消息包含 `"CelestialTreeClient"`
- **`PersistedErrorRecord` 未在此文件测试**（该类型在 `test_types.py` 中覆盖）

## 运行方式

```bash
# 全部执行
pytest tests/utils/test_errors.py -v

# 仅运行配置类异常测试
pytest tests/utils/test_errors.py -k "config or option or execution or stage or log or schedule" -v

# 仅运行图结构异常测试
pytest tests/utils/test_errors.py -k "graph or duplicate or unknown" -v

# 仅运行运行时异常测试
pytest tests/utils/test_errors.py -k "runtime or init or timeout or unconsumed" -v
```

## 性能参考

| 测试类 | 耗时 |
|--------|------|
| `TestUtilErrors` | ~0.05s |

## 重要细节

- 异常继承体系设计为 `CelestialFlowError → ConfigurationError → InvalidOptionError → {具体错误}`，确保捕获层级灵活。
- `InvalidOptionError` 自动将 `allowed` 转为元组存储，并格式化为带提示的错误消息。

## 注意事项

- 所有框架抛出的异常均应继承自 `CelestialFlowError`，便于用户统一捕获。
- 相关实现位于 `src/celestialflow/runtime/util_errors.py`。
