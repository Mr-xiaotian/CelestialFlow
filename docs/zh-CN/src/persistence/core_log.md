# 日志持久化 (Log Persistence)

> 📅 最后更新日期: 2026/05/24

`celestialflow.persistence` 模块提供了一个多进程安全的日志系统，旨在解决多进程环境下的日志统一收集、格式化和持久化问题。

核心组件包括 `LogSpout` 和 `LogInlet`。

## 架构设计

与错误持久化类似，日志系统也采用了 **Logger-Listener** 模式：

1.  **LogInlet (生产者)**:
    -   包装类，被各个 Worker 线程持有。
    -   提供丰富的语义化方法（如 `task_success`, `start_stage` 等）。
    -   将日志消息和级别封装后放入线程安全队列 (`queue.Queue`)。
    -   支持基于日志级别的过滤，减少不必要的通信。

2.  **LogSpout (消费者)**:
    -   运行在独立守护线程中。
    -   从队列中取出日志记录，将其写入文件。

## 日志级别

系统支持以下标准日志级别（数值越大优先级越高）：

| 级别 | 值 | 说明 |
|------|----|------|
| TRACE | 0 | 最详细的追踪信息，如队列的 `put`/`get` 操作 |
| DEBUG | 10 | 调试信息，如任务输入等 |
| SUCCESS | 20 | 关键操作成功，如任务完成、拆分成功 |
| INFO | 30 | 一般信息，如阶段启动/结束、图结构打印 |
| WARNING | 40 | 警告信息，如任务重试、队列操作异常 |
| ERROR | 50 | 错误信息，如任务失败、循环异常 |
| CRITICAL | 60 | 严重错误 |

## LogSpout

`LogSpout` 负责日志文件的配置和写入线程的管理。

### 初始化

```python
listener = LogSpout()
listener.start()
```

启动后，日志将写入 `logs/task_logger({date}).log` 文件。

### 文件路径

```text
logs/
└── task_logger(2026-05-24).log
```

## LogInlet

`LogInlet` 提供了针对不同组件的专用日志方法，确保日志内容的结构化和一致性。

### 初始化

```python
sinker = LogInlet(log_queue, log_level="SUCCESS")
```

-   `log_queue`: 也就是 `LogSpout.get_queue()` 返回的队列。
-   `log_level`: 设置该 Inlet 的最低日志级别，低于此级别的日志将不会被发送到队列。

### 方法分类

所有方法按组件域分组如下：

#### 任务图 (Graph)

| 方法 | 日志级别 | 说明 |
|------|---------|------|
| `start_graph(structure_list)` | INFO | 记录任务图启动及结构信息 |
| `end_graph(use_time)` | INFO | 记录任务图结束及耗时 |

#### 分层调度 (Layer)

| 方法 | 日志级别 | 说明 |
|------|---------|------|
| `start_layer(layer, layer_level)` | INFO | 记录分层的启动 |
| `end_layer(layer, use_time)` | INFO | 记录分层的结束及耗时 |

#### 阶段节点 (Stage)

| 方法 | 日志级别 | 说明 |
|------|---------|------|
| `start_stage(name, stage_mode, exec_mode, max_workers)` | INFO | 记录节点启动 |
| `end_stage(name, stage_mode, exec_mode, use_time, success_num, failed_num, duplicated_num)` | INFO | 记录节点结束及统计 |

#### 执行器 (Executor)

| 方法 | 日志级别 | 说明 |
|------|---------|------|
| `start_executor(name, func_name, task_num, exec_mode_desc)` | INFO | 记录执行器启动 |
| `end_executor(name, func_name, exec_mode, use_time, success_num, failed_num, duplicated_num)` | INFO | 记录执行器结束及统计 |

#### 任务生命周期 (Task)

| 方法 | 日志级别 | 说明 |
|------|---------|------|
| `task_input(func_name, task_repr, source, input_id)` | DEBUG | 记录任务进入输入队列 |
| `task_success(func_name, task_repr, exec_mode, result_repr, use_time, parent_id, success_id)` | SUCCESS | 记录任务成功完成 |
| `task_retry(func_name, task_repr, retry_times, exception, parent_id, retry_id)` | WARNING | 记录任务失败但触发重试 |
| `task_error(func_name, task_repr, exception, parent_id, error_id)` | ERROR | 记录任务失败且无法重试 |
| `task_duplicate(func_name, task_repr, parent_id, duplicate_id)` | WARNING | 记录检测到重复任务 |

#### Split 拆分 (Splitter)

| 方法 | 日志级别 | 说明 |
|------|---------|------|
| `split_trace(func_name, part_index, part_total, parent_id, split_id)` | TRACE | 记录 split 子任务分发 |
| `split_success(func_name, task_repr, split_count, use_time)` | SUCCESS | 记录 split 成功 |

#### Router 路由 (Router)

| 方法 | 日志级别 | 说明 |
|------|---------|------|
| `route_success(func_name, task_repr, target_node, use_time, parent_id, route_id)` | SUCCESS | 记录任务路由成功 |

#### 终止信号 (Termination)

| 方法 | 日志级别 | 说明 |
|------|---------|------|
| `termination_input(func_name, source, termination_id)` | DEBUG | 记录终止信号输入 |
| `termination_merge(func_name, parent_ids, termination_id)` | TRACE | 记录终止信号合并 |

#### 队列操作 (Queue)

| 方法 | 日志级别 | 说明 |
|------|---------|------|
| `put_item(item_type, item_id, in_name, out_name)` | TRACE | 记录队列 put 操作 |
| `put_item_error(in_name, out_name, exception)` | WARNING | 记录队列 put 失败 |
| `get_item(item_type, item_id, in_name, out_name)` | TRACE | 记录队列 get 操作 |
| `get_item_error(in_name, out_name, exception)` | WARNING | 记录队列 get 失败 |

#### 上报器 (Reporter)

| 方法 | 日志级别 | 说明 |
|------|---------|------|
| `stop_reporter()` | DEBUG | 记录上报器停止 |
| `loop_failed(exception)` | ERROR | 记录上报器循环错误 |
| `pull_interval_failed(exception)` | WARNING | 记录拉取上报间隔失败 |
| `pull_history_limit_failed(exception)` | WARNING | 记录拉取历史限制失败 |
| `pull_tasks_failed(exception)` | WARNING | 记录拉取任务注入失败 |
| `inject_tasks_success(target_node, task_datas)` | INFO | 记录任务注入成功 |
| `inject_tasks_failed(target_node, task_datas, exception)` | WARNING | 记录任务注入失败 |
| `push_errors_failed(exception)` | WARNING | 记录推送错误信息失败 |
| `push_status_failed(exception)` | WARNING | 记录推送状态信息失败 |
| `push_structure_failed(exception)` | WARNING | 记录推送结构信息失败 |
| `push_analysis_failed(exception)` | WARNING | 记录推送分析信息失败 |
| `push_summary_failed(exception)` | WARNING | 记录推送摘要信息失败 |
| `push_history_failed(exception)` | WARNING | 记录推送历史信息失败 |

### 使用示例

```python
# 图生命周期
sinker.start_graph(["NodeA -> NodeB", "NodeB -> NodeC"])
sinker.end_graph(12.34)

# 阶段周期
sinker.start_stage("ProcessStage", "thread", "thread", 4)
sinker.end_stage("ProcessStage", "thread", "thread", 5.2, 100, 2, 0)

# 执行器周期
sinker.start_executor("Executor1", "process_func", 50, "thread")
sinker.end_executor("Executor1", "process_func", "thread", 4.8, 48, 1, 1)

# 任务生命周期
sinker.task_input("process_func", "task_1", "queue", 1)
sinker.task_success("process_func", "task_1", "thread", "OK", 0.05, 1, 2)
sinker.task_retry("process_func", "task_2", 1, TimeoutError("timeout"), 1, 3)
sinker.task_error("process_func", "task_3", ValueError("bad"), 1, 4)
sinker.task_duplicate("process_func", "task_2", 1, 5)

# 队列操作
sinker.put_item("task", 1, "StageA", "StageB")
sinker.put_item_error("StageA", "StageB", ConnectionError("fail"))
sinker.get_item("task", 1, "StageA", "StageB")
sinker.get_item_error("StageA", "StageB", ConnectionError("fail"))

# 终止信号
sinker.termination_input("process_func", "queue", 1)
sinker.termination_merge("process_func", [1, 2], 3)

# 上报器事件
sinker.inject_tasks_success("StageA", ["task_10", "task_11"])
sinker.inject_tasks_failed("StageA", ["task_10"], RuntimeError("conflict"))
sinker.push_errors_failed(ConnectionError("timeout"))
sinker.push_history_failed(ConnectionError("timeout"))
```

通过使用这些专用方法，而不是通用的 `info()` 或 `debug()`，可以确保生成的日志易于阅读和机器解析。
