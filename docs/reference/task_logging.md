# TaskLogging

TaskLogging 模块提供了一个多进程安全的日志系统，基于 `loguru` 构建。

## 架构

为了支持多进程环境下的日志统一收集和写入，系统采用了 **Logger-Listener** 模式：

- **LogListener**: 运行在独立的守护线程中，持有一个 `MPQueue`（多进程队列）。它负责从队列中读取日志记录，并写入文件。
- **TaskLogger**: 包装类，被各个 Worker 进程持有。它将日志消息放入 `LogListener` 的队列中，而不是直接写文件。

## 日志级别

支持标准的日志级别：

- `TRACE` (0)
- `DEBUG` (10)
- `SUCCESS` (20)(default)
- `INFO` (30)
- `WARNING` (40)
- `ERROR` (50)
- `CRITICAL` (60)

## 日志文件

日志文件默认保存在 `logs/` 目录下，文件名格式为 `task_logger(YYYY-MM-DD).log`。

## 结构化日志

`TaskLogger` 提供了多种专用方法来记录特定事件，确保日志格式统一且易于解析：

- `start_executor` / `end_executor`
- `start_stage` / `end_stage`
- `task_input` / `task_success` / `task_error` / `task_retry`
- `split_trace` / `split_success`
- `route_success`

这些方法会自动附带上下文信息（如函数名、任务ID、耗时等）。
