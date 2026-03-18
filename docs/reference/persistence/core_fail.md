# 错误持久化 (Fail Persistence)

`celestialflow.persistence` 模块提供了一套稳健的错误收集与持久化机制，确保在多进程并发执行任务时，所有的异常信息都能被安全、有序地记录下来，供后续分析或重试使用。

核心组件包括 `FailListener` 和 `FailSinker`。

## 架构设计

系统采用了 **生产者-消费者** 模式来处理错误日志：

1.  **FailSinker (生产者)**:
    -   被各个 Worker 进程（或线程）持有。
    -   负责将错误信息、任务元数据封装成字典。
    -   将封装好的数据放入一个多进程安全的队列 (`multiprocessing.Queue`) 中。

2.  **FailListener (消费者)**:
    -   运行在主进程的一个独立守护线程中。
    -   持续监听队列，一旦有新的错误记录，立即将其写入本地文件。
    -   文件格式为 JSONL (JSON Lines)，便于流式读取和处理。

这种设计避免了多进程直接竞争写文件锁的问题，保证了高性能和数据完整性。

## FailListener

`FailListener` 负责管理错误日志文件的创建和写入。

### 初始化与启动

```python
listener = FailListener(error_source="graph_errors")
listener.start()
```

-   `error_source`: 错误来源标识，将作为文件名的一部分。
-   启动后，会在 `./fallback/{date}/` 目录下创建一个以 `{error_source}({time}).jsonl` 命名的文件。

### 文件路径

错误日志默认保存在 `./fallback/` 目录下，按日期归档：

```text
./fallback/
└── 2023-10-27/
    └── graph_errors(14-30-05-123).jsonl
```

### 停止监听

```python
listener.stop()
```

发送终止信号到队列，等待后台线程处理完剩余数据后安全退出。

## FailSinker

`FailSinker` 是向错误队列发送数据的接口。

### 记录任务错误

当任务执行失败且无法重试时，`TaskExecutor` 会调用 `task_error` 方法记录错误：

```python
sinker.task_error(
    ts=time.time(),
    stage_tag="MyStage",
    error=ValueError("Invalid input"),
    err_id="err-12345",
    task=[1, 2, 3]
)
```

记录的 JSONL 行包含以下字段：
-   `timestamp`: 错误发生的时间（ISO 格式）
-   `stage`: 发生错误的阶段标签
-   `error_repr`: 错误信息的字符串表示（截断）
-   `task_repr`: 任务数据的字符串表示（截断）
-   `error`: 完整的错误类型和信息
-   `task`: 原始任务数据
-   `error_id`: 错误的唯一标识符
-   `ts`: 原始时间戳

### 记录元数据

`FailSinker` 还支持记录一些元数据，帮助还原当时的执行环境：

-   `start_graph(structure_json)`: 记录任务图的结构信息。
-   `start_executor(executor_tag)`: 记录执行器的启动信息。

```python
sinker.start_graph({...})
```

## 数据恢复

由于错误日志采用标准的 JSONL 格式，你可以轻松编写脚本读取这些文件，提取失败的任务数据进行重试或分析。框架提供的 `celestialflow.task_tools.load_jsonl_logs` 函数可以辅助读取。
