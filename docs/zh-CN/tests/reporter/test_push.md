# tests/reporter/test_push.py

> 📅 最后更新日期: 2026/11/13

## 作用

验证 `celestialflow.reporter.core_push` 的推送链路：

- `PushInlet.on_event(event)` 用 `match` 把 `GraphStartEvent` / `GraphEndEvent` / `TaskFailEvent` 映射为对应 `kind` 的 `PushRecord`，经 `send()` 入队；
- `PushSpout` 按记录类型把记录 POST 到不同端点，非 2xx 时抛 `ReporterError`；
- 后台线程消费队列、单条失败不致死线程、`stop()` 时关闭 HTTP 会话；
- `NullPushSpout` 不建立 HTTP 会话并直接丢弃记录。

## 核心测试对象

| 对象 | 来源 | 说明 |
|------|------|------|
| `PushInlet` | `celestialflow.reporter` | 观察者入口 `on_event()` + 入队方法 `send()`；另含 `push_snapshot()` |
| `PushSpout` | `celestialflow.reporter` | 推送 spout，`PushRecord` 队列消费者 |
| `NullPushSpout` | `celestialflow.reporter` | 空实现 spout |
| `PushRecord` | `celestialflow.reporter.core_push` | 冻结 dataclass，按 `kind` 复用不同字段 |
| `GraphStartEvent` / `GraphEndEvent` / `TaskFailEvent` | `celestialflow.observer` | 入队映射的三种事件 |
| `ReporterError` | `celestialflow.runtime.util_errors` | 非 2xx 响应的预期异常 |
| `wait_until` | `tests/conftest.py` | 轮询等待后台线程消费完成（默认 5 秒超时） |

## 关键 fixture 与假对象

| 名称 | 用途 |
|------|------|
| `FakePostResponse` | 模拟响应：可配置 `ok` 与 `status_code` |
| `FakePushSession` | `requests.Session` 替身：`post()` 记录 `(url, json, timeout)`；`close()` 置 `closed = True` |
| `_fail_event(...)` | 构造 `TaskFailEvent(node, task, f"({task})", exception, task_id=1, error_id)`，默认 `error_id=21`、`node="s1"`、`task="data1"`、`ValueError("oops")` |
| `_start_event()` | 构造带图元信息的 `GraphStartEvent`（`g1` / `thread` / `is_dag=True` / 两节点及 `node_meta`） |
| `_end_event()` | 构造 `GraphEndEvent(graph="g1", end_time=456.0, elapsed=1.5)` |
| `_dequeue(spout)` | 从 `spout.get_queue()` 取一条记录并断言类型为 `PushRecord` |

## 测试覆盖矩阵

| 用例 | 覆盖目标 |
|------|---------|
| `test_inlet_maps_task_fail_event` | 失败事件 → `kind="task_fail"`，`event_id` / `node` / `task_json` / `error_type` / `error_message` / `ts` |
| `test_inlet_maps_graph_start_event` | 图启动事件 → `kind="graph_start"`，图元字段完整透传 |
| `test_inlet_maps_graph_end_event` | 图结束事件 → `kind="graph_end"`，`end_time` / `elapsed` |
| `test_spout_pushes_task_fail_to_push_error_endpoint` | `POST /api/push_error` 及载荷字段 |
| `test_spout_pushes_graph_start_to_graph_meta_endpoint` | `POST /api/push_graph_meta` 及顶层图元字段 |
| `test_spout_pushes_graph_end_to_shutdown_endpoint` | `POST /api/shutdown_session`，载荷仅 `session_id` |
| `test_handle_record_raises_reporter_error_on_failure` | 非 2xx 时 `_handle_record` 抛 `ReporterError` |
| `test_spout_thread_drains_records_and_closes_session` | 后台线程消费两条记录、队列清空、`stop()` 后会话关闭 |
| `test_spout_thread_survives_push_failure` | 持续失败不致死线程，记录仍被消费，线程可正常停止 |
| `test_null_spout_discards_records` | `NullPushSpout` 不创建 session，记录被排空 |

## 关键行为细节

### 事件 → 记录映射

| 事件 | `PushRecord.kind` | 使用字段 |
|------|-------------------|---------|
| `GraphStartEvent` | `"graph_start"` | `graph`、`graph_mode`、`start_time`、`is_dag`、`nodes`、`edges`、`source_nodes`、`node_meta` |
| `GraphEndEvent` | `"graph_end"` | `graph`、`end_time`、`elapsed` |
| `TaskFailEvent` | `"task_fail"` | `event_id ← error_id`、`node`、`task_json ← to_persisted_payload(task)`、`error_type ← exception 类型名`、`error_message ← str(exception)`、`ts ← time.time()` |
| 其它事件 | 不入队 | `match` 的 `case _: pass` |

- `PushInlet` 继承 `BaseInlet` 与 `Observer`，事件入口统一为 `on_event(event)`；记录入队统一走 `send()`（`BaseInlet` 提供，写入绑定的 spout 队列）。
- `task_json` 经过 `to_persisted_payload`，因此测试中 `task={"value": 1}` 得到同构字典；不可序列化对象会被投影为可持久化形态。
- `error_id` 在记录中字段名为 `event_id`。

### 记录 → 端点

| `kind` | 端点 | 载荷要点 |
|--------|------|---------|
| `graph_start` | `{base_url}/api/push_graph_meta` | `session_id` + 全部图元字段（顶层平铺） |
| `graph_end` | `{base_url}/api/shutdown_session` | 仅 `{"session_id": ...}`，**不发送** `end_time` / `elapsed` |
| `task_fail` | `{base_url}/api/push_error` | `session_id`、`event_id`、`node`、`task_json`、`error_type`、`error_message`、`ts` |
| `snapshot` | `{base_url}/api/push_snapshot` | 见 `test_snapshot.md` |

- 测试断言 `payload["timestamp"]` 之类的字段不在本文件覆盖范围内；本文件只覆盖上述三类事件记录。
- `graph_end` 的语义是“会话下线通知”：服务端收到后把会话标记为结束，会话数据与错误库仍保留。
- 每次 POST 都带 `timeout=self.timeout`（构造默认 `3.0`）；测试只解包为 `_timeout`，不改写断言。

### 后台线程与失败隔离

- `PushSpout.start()` 通过 `BaseSpout._before_start()` 创建 `requests.Session`，随后启动 daemon 线程循环 `get_queue()`。
- `_handle_record` 抛出的 `ReporterError` 由 `BaseSpout._spout` 的 `try/except Exception` 捕获并打印，线程继续消费；`get_pending_count()` 在 `finally` 中递减。
- `stop()` 向队列放入终止信号并 `join`（最多 5 秒），线程退出后 `_after_stop()` 关闭 session。
- 线程用例用 `monkeypatch.setattr(push_module.requests, "Session", lambda: session)` 注入假会话，并通过 `wait_until(lambda: len(session.posts) == 2 and spout.get_pending_count() == 0)` 等待消费完成。
- `test_spout_thread_survives_push_failure` 使用 `ok=False` 的会话，只等待 `get_pending_count() == 0`，最后断言 `session.closed`，证明失败不会阻塞停止。

### Null 版本

`NullPushSpout` 覆写 `_handle_record` 为直接丢弃，且没有覆写 `_before_start`，因此不创建任何 `requests.Session`。测试把 `requests.Session` 替换为 `pytest.fail(...)`，若被调用会立刻失败；随后启动、入队两条记录、等待队列排空并停止。

## 运行方式

```bash
# 全部执行
uv run pytest tests/reporter/test_push.py -v

# 仅入队映射
uv run pytest tests/reporter/test_push.py -k "inlet_maps" -v

# 仅端点推送
uv run pytest tests/reporter/test_push.py -k "endpoint" -v

# 仅后台线程
uv run pytest tests/reporter/test_push.py -k "thread or null" -v
```

## 注意事项

- 非线程用例直接给 `spout._session` 赋假会话以绕过 `start()`；这依赖被测实现的私有字段名 `_session`，若重命名需同步修改测试。
- 线程用例依赖 `tests/conftest.py` 的 `wait_until`（通过根 `conftest` 导入），默认超时 5 秒；实际耗时应远小于该值。
- 队列中可能残留已入队但未消费的记录，测试通过 `spout.get_queue().get()` 同步取出，不启动线程。
- 相关实现见 `src/celestialflow/reporter/core_push.py`，语义说明见 `docs/zh-CN/src/reporter/core_push.md`。
