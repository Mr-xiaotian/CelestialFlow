# 运行时异常测试 (test_errors.py)

> 最后更新日期: 2026/06/05

## 作用
验证 `celestialflow.runtime.util_errors` 中的自定义异常体系，确保异常继承关系、默认消息和附加字段都符合预期。

## 覆盖点
- 基础异常：`CelestialFlowError`、`ConfigurationError`、`RuntimeStateError`。
- 选项错误：`InvalidOptionError`、`ExecutionModeError`、`StageModeError`、`ScheduleModeError`、`LogLevelError`。
- 图与运行时错误：`DuplicateNodeError`、`UnknownNodeError`、`InitializationError`、`UnconsumedError`。
- 外部依赖错误：`ReporterError`、`RemoteWorkerError`、`CelestialTreeConnectionError`。

## 关键场景
- 检查异常是否继承自正确的父类。
- 检查 `field`、`value`、`allowed` 等附加字段是否被保存。
- 检查默认文案与自定义错误消息是否可读。

## 运行方式

```bash
pytest tests/runtime/test_errors.py -v
pytest tests/runtime/test_errors.py -k "invalid_option or connection" -v
```
