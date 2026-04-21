# test_queue.py 测试说明

## 测试目标

验证 `TaskInQueue`（任务输入队列）和 `TaskOutQueue`（任务输出队列）的核心行为，包括：任务信封的入队/出队、终止信号的合并逻辑、异常来源校验、队列清空（drain）、广播/定向发送及动态队列管理。这两个类是 CelestialFlow 数据流引擎的管道层，其可靠性直接决定了图调度的正确性。

## 测试范围

| 测试类 | 用例数 | 覆盖点 |
|--------|--------|--------|
| `TestTaskInQueue` | 5 | put/get、终止信号直接退出、多源合并、未知来源报错、drain |
| `TestTaskOutQueue` | 4 | 广播、定向发送、动态添加队列、重复标签校验 |

### 关键用例详解

#### `test_put_and_get_task`
- **目标**：验证 `TaskEnvelope` 能正确入队和出队，且数据不丢失。
- **机制**：底层使用 Python 标准库 `queue.Queue`（线程安全）。

#### `test_input_termination_direct_exit`
- **目标**：当 `source == "input"` 时，终止信号应立即返回 `TerminationIdPool`，不等待其他上游。
- **设计**：模拟外部（如用户通过 Web 接口）直接注入的终止信号。

#### `test_multi_source_termination_merge`
- **目标**：多上游 DAG 场景下，所有上游都发送终止信号后才合并为一个 `TerminationIdPool` 返回。
- **设计**：队列 tags 为 `["src_a", "src_b"]`，依次注入两个终止信号。
- **断言**：合并后的 `ids` 包含 `[10, 20]`。
- **注意**：第一次注入后 `get()` 会阻塞等待，直到第二次注入才返回。这是框架实现 staged / eager 终止语义的核心。

#### `test_unknown_source_termination_raises`
- **目标**：来源不在 `queue_tags` 中的终止信号应抛出 `ValueError`。
- **安全意义**：防止恶意或错误的上游节点发送伪造终止信号导致过早关闭。

#### `test_drain_returns_remaining_tasks`
- **目标**：`drain()` 应非阻塞地清空队列，返回所有剩余 `TaskEnvelope`，并记录终止信号但不返回。
- **应用场景**：图执行结束后的资源清理阶段，收集未消费任务以便持久化到失败日志。

#### `test_put_broadcasts_to_all`
- **目标**：`TaskOutQueue.put()` 向所有已注册的输出队列广播同一信封。
- **应用场景**：`TaskGraph` 中的 fan-out（扇出）边。

#### `test_put_target_single_queue`
- **目标**：`put_target(envelope, tag="b")` 仅发送到指定标签的队列。
- **应用场景**：`TaskRouter` 的路由分发。

## 依赖

| 依赖 | 说明 |
|------|------|
| `pytest` | 测试框架 |
| `celestialflow.runtime.core_queue` | `TaskInQueue`、`TaskOutQueue` |
| `celestialflow.persistence.core_log` | `LogSpout`、`LogInlet`（fixture 依赖） |

## 可能的问题与注意事项

### 1. `get()` 的阻塞性
`TaskInQueue.get()` 是阻塞调用。在单元测试中，如果终止信号逻辑有 bug（如永远等不到某个上游的终止信号），测试会挂死直到 pytest 超时。

**当前超时保护**：pytest 默认函数超时由外部配置（如 `pytest-timeout` 插件）控制。建议在 CI 中安装 `pytest-timeout`：
```bash
pip install pytest-timeout
pytest tests/test_queue.py --timeout=10
```

### 2. `drain` 与 `get` 的竞态
`drain()` 使用 `queue.get_nowait()` 非阻塞清空。如果在 `drain()` 执行的同时，另一个线程/进程正在 `put()`，可能出现：
- `drain()` 结束后仍有少量任务残留
- 终止信号未被完全记录

**建议**：`drain()` 仅在所有上游已确认停止、不再有新数据时调用（框架在 `_finalize_nodes` 中保证此条件）。

### 3. `LogSpout` 的文件副作用
测试 fixture 中会启动 `LogSpout`，它会创建 `logs/task_logger(YYYY-MM-DD).log` 文件。虽然测试使用 `log_level="ERROR"` 以减少写入，但仍可能产生空日志文件。

**清理建议**：在 CI 的 `after_script` 中清理日志：
```bash
rm -rf logs/
```

### 4. `queue_tags` 的顺序敏感性
`TaskInQueue._merge_termination()` 按照 `queue_tags` 的顺序合并 ID 列表。虽然当前测试使用 `sorted()` 比较，但生产代码中终止 ID 的顺序可能影响 CelestialTree 中的 provenance 树展示。

### 5. 异步队列未覆盖
当前测试仅覆盖了同步队列（`queue.Queue`）。`TaskInQueue` 和 `TaskOutQueue` 也支持 `asyncio.Queue`，但以下路径未测试：
- `put_async()` / `get_async()`
- `put_channel_async()`

**建议补充**：
```python
@pytest.mark.asyncio
async def test_put_async():
    q = asyncio.Queue()
    in_queue = TaskInQueue(q, ...)
    await in_queue.put_async(envelope)
```

### 6. `TaskOutQueue` 的 `put_target` 异常
如果 `tag` 不存在于 `_tag_to_idx`，`put_target()` 会抛出 `KeyError` 而非自定义异常。当前未在测试中覆盖此失败路径。

## 运行方式

```bash
pytest tests/test_queue.py -v
```

所有用例执行时间 `< 500ms`。

## 相关文件

- `src/celestialflow/runtime/core_queue.py`：被测实现
- `src/celestialflow/runtime/core_envelope.py`：`TaskEnvelope`
- `src/celestialflow/runtime/util_types.py`：`TerminationSignal`、`TerminationIdPool`
- `tests/test_graph.py`：在图级别验证队列集成
