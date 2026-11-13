# tests/persist/test_log.py

> 📅 最后更新日期: 2026/11/13

## 作用

验证 `celestialflow.persist.core_log` 中 `LogObserver` 的日志落盘能力：观察者把图 / 节点 / 任务 / 终止信号事件翻译为 `LogRecord`，经 `LogInlet.send()` 投递到后台 `LogSpout`，异步写入日志文件；测试同时校验日志级别过滤与 `[task_id->event_id*]` 事件 ID 标记。

## 核心测试对象

| 类 / 对象 | 来源 | 说明 |
|-----------|------|------|
| `LogObserver` | `celestialflow.persist.core_log` | 观察者门面：构造参数为 `metrics_view` 与 `log_level`，内部创建并绑定 `LogSpout` / `LogInlet`，提供 `start()` / `stop()` / `log_path`，在 `on_event(event)` 中按事件类型记录日志 |
| `LogRecord` | `celestialflow.persist.core_log` | 不可变 dataclass：`timestamp` / `level` / `message` |
| `LogInlet` | `celestialflow.persist.core_log` | 记录入口，仅提供 `send(record)`，把记录放入绑定 spout 的队列 |
| `LogSpout` | `celestialflow.persist.core_log` | 后台线程消费队列，把记录以 `"{timestamp} {level} {message}"` 逐行写入日志文件；路径通过 `log_path` 获取 |
| `MetricsObserver` | `celestialflow.observer` | 作为 `MetricsView` 传入，供 `LogObserver` 在节点启动 / 结束时读取任务数统计 |
| 事件类型 | `celestialflow.observer` | `GraphStartEvent` / `TaskRetryEvent` / `GraphEndEvent` / `NodeStartEvent` / `TaskSkipEvent` |

## 事件与日志级别

| 事件 | 级别 | 关键内容 |
|------|:----:|---------|
| `GraphStartEvent` | `INFO` | 图名、`graph_mode`，并用 `render_structure_list()` 展开结构行 |
| `GraphEndEvent` | `INFO` | 图名与耗时 |
| `NodeStartEvent` | `INFO` | 节点名、从 `metrics_view` 读取的 `input_total`、`execution_mode-max_workers` |
| `NodeEndEvent` | `INFO` | 节点名、执行模式、耗时、成功 / 失败 / 跳过数 |
| `TaskInputEvent` | `DEBUG` | 任务表示、来源（`from_node` 或 `external`）、`[input_id*]` |
| `TaskSuccessEvent` | `SUCCESS` | 任务表示、结果、耗时、`[task_id->success_id*]` |
| `TaskFailEvent` | `ERROR` | 异常类型与消息、`[task_id->error_id*]` |
| `TaskSkipEvent` | `SUCCESS` | 任务表示、`[task_id->skip_id*]` |
| `TaskRetryEvent` | `WARNING` | 重试次数、异常类型、`[task_id*]` |
| `TerminationInputEvent` | `DEBUG` | `[termination_id*]` |
| `TerminationMergeEvent` | `TRACE` | `[parent_ids->termination_id*]` |

> `LogObserver` 会丢弃低于 `log_level` 的事件日志；`log_level` 在构造时 `upper()` 并校验，非法值抛 `InvalidOptionError`。默认值来自 `celestialflow.runtime.util_log_level.DEFAULT_LOG_LEVEL`（当前为 `"INFO"`）。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestLogPersistence` | 2 | 完整日志生命周期、跳过日志 |

## 关键测试场景

### `test_log_persistence`

- 构造 `LogObserver(MetricsObserver(), log_level='INFO')`，调用 `start()` 启动后台写入线程。
- 依次发送 `GraphStartEvent`（图名 / 模式 / 结构列表 / 节点元信息）、`TaskRetryEvent`（携带 `ValueError`）、`GraphEndEvent`、`NodeStartEvent`。
- 通过 `wait_until` 轮询等待日志文件存在，且同时包含结构行 `| node |` 与任务表示 `hello world`。
- `finally` 中 `stop()`；最终断言日志文件中同时存在 `INFO` 与 `WARNING` 级别标记。

### `test_skip_log`

- 构造 `LogObserver(MetricsObserver(), log_level='SUCCESS')`。
- 发送 `TaskSkipEvent("node", "hello world", "hello world", 7, 8)`。
- `wait_until` 等待日志文件包含 `hello world`。
- 断言日志包含 `hello world`、`skipped`、`[7->8*]` 与 `SUCCESS` 级别标记。

## 数据流

```mermaid
flowchart LR
    E[观测事件] --> O[LogObserver.on_event]
    O -->|_log 级别过滤| R[LogRecord]
    R --> I[LogInlet.send]
    I -->|队列| S[LogSpout 后台线程]
    S -->|逐行追加| F[logs/flow_log YYYY-MM-DD .log]
```

## 运行方式

```bash
pytest tests/persist/test_log.py -v
pytest tests/persist/test_log.py -k "log_persistence" -v
pytest tests/persist/test_log.py -k "skip" -v
```

## 注意事项

- 测试使用 `monkeypatch.chdir(tmp_path)` 切换工作目录，日志写入临时目录下的 `logs/flow_log(<日期>).log`。
- 日志文件路径通过 `LogObserver.log_path` 属性（转发自 `LogSpout.log_path`）获取；spout 尚未启动时为 `None`。
- `LogInlet` 只继承 `BaseInlet` 并暴露 `send(record)`，事件经队列异步写入文件，测试用 `wait_until` 规避线程时序抖动。
- 两个用例都显式传入 `log_level`，未覆盖默认值分支。
- 相关实现位于 `src/celestialflow/persist/core_log.py`。
