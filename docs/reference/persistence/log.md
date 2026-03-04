# 日志持久化 (Log Persistence)

`celestialflow.persistence` 模块提供了一个多进程安全的日志系统，基于 `loguru` 构建，旨在解决多进程环境下的日志统一收集、格式化和持久化问题。

核心组件包括 `LogListener` 和 `LogSinker`。

## 架构设计

与错误持久化类似，日志系统也采用了 **Logger-Listener** 模式：

1.  **LogSinker (生产者)**:
    -   包装类，被各个 Worker 进程持有。
    -   提供丰富的语义化方法（如 `task_success`, `start_stage` 等）。
    -   将日志消息和级别封装后放入多进程队列 (`multiprocessing.Queue`)。
    -   支持基于日志级别的过滤，减少不必要的跨进程通信。

2.  **LogListener (消费者)**:
    -   运行在主进程的独立守护线程中。
    -   从队列中取出日志记录，使用 `loguru` 将其写入文件。
    -   统一管理日志文件的轮转和格式。

## 日志级别

系统支持以下标准日志级别（数值越大优先级越高）：

-   **TRACE** (0): 最详细的追踪信息，如队列的 `put`/`get` 操作。
-   **DEBUG** (10): 调试信息，如进程退出、任务输入等。
-   **SUCCESS** (20): 关键操作成功，如任务完成、拆分成功。
-   **INFO** (30): 一般信息，如阶段启动/结束、图结构打印。
-   **WARNING** (40): 警告信息，如任务重试、队列操作异常。
-   **ERROR** (50): 错误信息，如任务失败、循环异常。
-   **CRITICAL** (60): 严重错误。

## LogListener

`LogListener` 负责日志文件的配置和写入线程的管理。

### 初始化

```python
listener = LogListener()
listener.start()
```

启动后，日志将写入 `logs/log_sinker({date}).log` 文件。

### 文件路径

```text
logs/
└── log_sinker(2023-10-27).log
```

## LogSinker

`LogSinker` 提供了针对不同组件的专用日志方法，确保日志内容的结构化和一致性。

### 初始化

```python
sinker = LogSinker(log_queue, log_level="SUCCESS")
```

-   `log_queue`: 也就是 `LogListener.get_queue()` 返回的队列。
-   `log_level`: 设置该 Sinker 的最低日志级别，低于此级别的日志将不会被发送到队列。

### 常用方法

#### 任务执行 (Executor)
-   `start_executor(...)`: 记录执行器启动。
-   `end_executor(...)`: 记录执行器结束，包含耗时和统计信息。

#### 阶段与层级 (Stage & Layer)
-   `start_stage` / `end_stage`: 记录阶段的生命周期。
-   `start_layer` / `end_layer`: 记录分层调度中每一层的执行情况。

#### 任务生命周期 (Task)
-   `task_input`: 任务进入输入队列。
-   `task_success`: 任务成功完成，记录结果摘要和耗时。
-   `task_retry`: 任务失败但触发重试。
-   `task_error`: 任务失败且无法重试（最终失败）。
-   `task_duplicate`: 检测到重复任务。

#### 任务流转 (Flow)
-   `split_trace` / `split_success`: 记录任务拆分过程。
-   `route_success`: 记录任务路由结果。
-   `put_item` / `get_item`: 记录队列的底层操作（TRACE 级别）。

#### 报告器 (Reporter)
-   `push_*_failed`: 记录向 Web 服务器推送数据失败的警告。
-   `pull_*_failed`: 记录从 Web 服务器拉取配置失败的警告。

通过使用这些专用方法，而不是通用的 `info()` 或 `debug()`，可以确保生成的日志易于阅读和机器解析。
