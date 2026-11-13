# tests/runtime/test_queue.py

> 📅 最后更新日期: 2026/11/13

## 作用
验证任务在不同节点间流转的队列管理逻辑，包括任务的入队出队、终止信号的合并与广播、以及队列的动态扩展。

## 核心测试对象
- `TaskInQueue`: 包装 Python 标准 `queue.Queue`，负责多上游信号合并。
- `TaskOutQueue`: 负责向多个下游节点广播或定向发送任务。

## 关键测试场景

### `TestTaskInQueue` — 输入队列
`simple_queue` fixture 构造一个无上游来源的输入队列（仅 `out_name="test"`），供单源用例复用。

| 用例 | 覆盖目标 |
|------|----------|
| `test_put_and_get_task` | 基础存取：入队和出队 `TaskEnvelope`，任务与 ID 原样返回 |
| `test_input_termination_direct_exit` | 来源为 `"input"` 的 `TerminationSignal` 直接转换为只含该 ID 的 `TerminationIdPool` |
| `test_multi_source_termination_merge` | 两个上游各发一次终止信号后，`get()` 返回包含 `{10, 20}` 的合并 ID 池（断言时排序后比较；实现上未集齐所有上游时 `get()` 会继续等待） |
| `test_unknown_source_termination_raises` | 未知来源的终止信号抛出 `UnknownNodeError`（匹配 `"unknown queue source name"`） |
| `test_drain_returns_remaining_tasks` | `drain()` 清空队列并按入队顺序返回全部剩余任务，队列随之变空 |

### `TestTaskOutQueue` — 输出队列
输出队列使用标准库 `queue.Queue` 作为真实落点，验证广播/定向发送的可见结果。

| 用例 | 覆盖目标 |
|------|----------|
| `test_put_broadcasts_to_all` | `put()` 向所有下游队列广播同一信封 |
| `test_put_target_single_queue` | `put_target()` 只发送到指定队列，其余队列保持为空 |
| `test_add_queue` | 动态添加输出队列后，新队列同样收到广播 |
| `test_duplicate_queue_name_raises` | 重复目标名称抛出 `DuplicateNodeError`（匹配 `"duplicate queue target name"`） |

## 测试重点
- **信号同步**: 确保多上游环境下，节点不会因为某个上游提前结束而丢失其他上游的数据。
- **类型安全**: 验证从队列中获取的对象符合预期的 `TaskEnvelope` 或 `TerminationIdPool` 类型。
- **扇出逻辑**: 确保 `TaskOutQueue` 能高效处理一对多的数据分发。

## 运行方式

```bash
# 全部执行
uv run pytest tests/runtime/test_queue.py -v

# 仅运行输入队列测试
uv run pytest tests/runtime/test_queue.py::TestTaskInQueue -v

# 仅运行输出队列测试
uv run pytest tests/runtime/test_queue.py::TestTaskOutQueue -v

# 仅运行信号合并测试
uv run pytest tests/runtime/test_queue.py -k "termination" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskInQueue` / `TestTaskOutQueue` | < 0.1s（队列操作均在内存中完成） |

## 重要细节
- 使用 `TerminationIdPool` 汇总所有来源的终止 ID，方便后续溯源。
- `TaskInQueue.drain()` 只返回 `TaskEnvelope`，途中遇到的终止信号只记录到 `termination_dict`，不返回 ID 池。
- 重复来源名 / 重复目标名分别由 `add_source_name` 与 `add_queue` 抛出 `DuplicateNodeError`；本文件只覆盖后者。
- `test_duplicate_queue_name_raises` 验证了图结构定义的严谨性。

## 注意事项
- 队列机制是 CelestialFlow 异步非阻塞架构的核心支柱。
- 相关实现位于 `src/celestialflow/runtime/core_queue.py`。
