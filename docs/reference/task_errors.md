# TaskErrors

TaskErrors 模块定义了框架中使用的自定义异常类。

## 基类

- `CelestialFlowError`: 所有自定义异常的基类。

## 配置相关异常

- `ConfigurationError`: 配置错误基类。
- `InvalidOptionError`: 某个配置项取值不合法。
- `ExecutionModeError`: `execution_mode` 配置错误（支持 serial, thread, process, async）。
- `StageModeError`: `stage_mode` 配置错误（支持 serial, process）。
- `LogLevelError`: 日志级别配置错误。

## 运行时异常

- `RemoteWorkerError`: 远程 Worker（如 Go Worker）执行失败时抛出的异常。

## 错误处理策略

在 `TaskExecutor` 中，异常被分为两类：

1. **可重试异常**: 如果异常类型在 `retry_exceptions` 列表中，且重试次数未达上限，框架会自动重试该任务。
2. **不可重试异常**: 任务会被标记为失败，记录错误日志，并放入 `fail_queue`。

## 错误持久化

`TaskGraph` 会自动将所有未处理的错误（包括重试失败和 UnconsumedError）持久化到本地的 `fallback/` 目录下，格式为 JSONL。
每个错误记录包含：
- 时间戳
- 阶段标签
- 错误信息
- 原始任务数据
- 错误 ID
