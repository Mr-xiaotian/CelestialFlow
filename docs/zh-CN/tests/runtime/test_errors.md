# 运行时异常测试 (test_errors.py)

> 📅 最后更新日期: 2026/08/12

## 作用
验证 `celestialflow.runtime.util_errors` 中的自定义异常体系，确保异常继承关系、默认消息和附加字段都符合预期。

## 覆盖点
- 基础异常：`CelestialFlowError`。
- 配置与选项错误：`ConfigurationError`、`InvalidOptionError`（含 `field`、`value`、`allowed` 字段及自定义前缀）。
- 图结构错误：`GraphStructureError`、`DuplicateNodeError`、`UnknownNodeError`。
- 运行时与生命周期：`RuntimeStateError`、`InitializationError`、`CelestialFlowTimeoutError`（同时继承 `TimeoutError`）、`UnconsumedError`。
- 任务与逻辑：`TerminationMergeError`。
- 外部依赖：`ReporterError`、`RemoteWorkerError`。

## 测试覆盖矩阵

| 分类 | 用例数 | 覆盖异常 |
|------|--------|---------|
| 基础异常 | 1 | `CelestialFlowError` |
| 配置与选项 | 7 | `ConfigurationError`、`InvalidOptionError`（含自定义前缀、各种非法字段值） |
| 图结构 | 3 | `GraphStructureError`、`DuplicateNodeError`、`UnknownNodeError` |
| 运行时与生命周期 | 4 | `RuntimeStateError`、`InitializationError`、`CelestialFlowTimeoutError`、`UnconsumedError` |
| 外部服务与通信 | 2 | `RemoteWorkerError`、`ReporterError` |
| 任务与逻辑 | 1 | `TerminationMergeError` |
| **合计** | **18** | |

## 关键场景
- 检查异常是否继承自正确的父类（多继承链验证，如 `InvalidOptionError → ConfigurationError → CelestialFlowError`）。
- 检查 `field`、`value`、`allowed` 等附加字段是否被保存。
- 检查不同非法字段值（如 `execution_mode`、`stage_mode`、`log_level`、`schedule_mode`）均通过 `InvalidOptionError` 统一处理并暴露字段信息。
- 检查默认文案与自定义错误消息是否可读。

## 运行方式

```bash
pytest tests/runtime/test_errors.py -v
pytest tests/runtime/test_errors.py -k "invalid_option or execution_mode" -v
pytest tests/runtime/test_errors.py -k "timeout or termination or graph_structure" -v
```
