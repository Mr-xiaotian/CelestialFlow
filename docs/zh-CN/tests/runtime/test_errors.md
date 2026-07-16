# 运行时异常测试 (test_errors.py)

> 📅 最后更新日期: 2026/07/16

## 作用
验证 `celestialflow.runtime.util_errors` 中的自定义异常体系，确保异常继承关系、默认消息和附加字段都符合预期。

## 覆盖点
- 基础异常：`CelestialFlowError`。
- 选项错误：`InvalidOptionError`、`ExecutionModeError`、`StageModeError`、`ScheduleModeError`、`LogLevelError`，以及各自的字段（`field`、`value`、`allowed`）。
- 图结构错误：`GraphStructureError`、`DuplicateNodeError`、`UnknownNodeError`。
- 运行时与生命周期：`RuntimeStateError`、`InitializationError`、`CelestialFlowTimeoutError`（同时继承 `TimeoutError`）、`UnconsumedError`。
- 任务与逻辑：`TerminationMergeError`。
- 外部依赖：`ReporterError`、`RemoteWorkerError`。

## 测试覆盖矩阵

| 分类 | 用例数 | 覆盖异常 |
|------|--------|---------|
| 基础异常 | 1 | `CelestialFlowError` |
| 配置与选项 | 8 | `ConfigurationError`、`InvalidOptionError`（含自定义前缀）、`ExecutionModeError`（含自定义模式）、`StageModeError`、`LogLevelError`、`ScheduleModeError` |
| 图结构 | 3 | `GraphStructureError`、`DuplicateNodeError`、`UnknownNodeError` |
| 运行时与生命周期 | 4 | `RuntimeStateError`、`InitializationError`、`CelestialFlowTimeoutError`、`UnconsumedError` |
| 外部服务与通信 | 2 | `RemoteWorkerError`、`ReporterError` |
| 任务与逻辑 | 1 | `TerminationMergeError` |

## 关键场景
- 检查异常是否继承自正确的父类（多继承链验证，如 `InvalidOptionError → ConfigurationError → CelestialFlowError`）。
- 检查 `field`、`value`、`allowed` 等附加字段是否被保存。
- 检查默认文案与自定义错误消息是否可读。

## 运行方式

```bash
pytest tests/runtime/test_errors.py -v
pytest tests/runtime/test_errors.py -k "invalid_option or execution_mode" -v
pytest tests/runtime/test_errors.py -k "timeout or termination or graph_structure" -v
```
