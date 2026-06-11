# 运行时队列测试 (test_queue.py)

> 最后更新日期: 2026/06/11

## 作用
验证任务在不同节点（Stage）间流转的队列管理逻辑，包括任务的入队出队、终止信号的合并与广播、以及队列的动态扩展。

## 核心测试对象
- `TaskInQueue`: 包装 Python 标准 `queue.Queue`，负责多上游信号合并。
- `TaskOutQueue`: 负责向多个下游节点广播或定向发送任务。

## 关键测试场景

### `TestTaskInQueue` — 输入队列
| 用例 | 覆盖目标 |
|------|----------|
| `test_put_and_get_task` | 基础存取：入队和出队 `TaskEnvelope` |
| `test_input_termination_direct_exit` | 外部注入的 `TerminationSignal` 应直接返回 |
| `test_multi_source_termination_merge` | 多上游终止信号需全部到达后才合并返回 |
| `test_unknown_source_termination_raises` | 未知来源的终止信号抛出 `UnknownNodeError` |
| `test_drain_returns_remaining_tasks` | `drain()` 清空队列并返回全部剩余任务 |

### `TestTaskOutQueue` — 输出队列
| 用例 | 覆盖目标 |
|------|----------|
| `test_put_broadcasts_to_all` | `put()` 向所有下游队列广播 |
| `test_put_target_single_queue` | `put_target()` 只发送到指定队列 |
| `test_add_queue` | 动态添加输出队列 |
| `test_duplicate_queue_name_raises` | 重复目标名称抛出 `DuplicateNodeError` |

## 测试重点
- **信号同步**: 确保多上游环境下，节点不会因为某个上游提前结束而丢失其他上游的数据。
- **类型安全**: 验证从队列中获取的对象符合预期的 `TaskEnvelope` 或 `TerminationIdPool` 类型。
- **扇出逻辑**: 确保 `TaskOutQueue` 能高效处理一对多的数据分发。

## 运行方式

```bash
# 全部执行
pytest tests/runtime/test_queue.py -v

# 仅运行输入队列测试
pytest tests/runtime/test_queue.py -k "InQueue" -v

# 仅运行输出队列测试
pytest tests/runtime/test_queue.py -k "OutQueue" -v

# 仅运行信号合并测试
pytest tests/runtime/test_queue.py -k "termination" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskInQueue` / `TestTaskOutQueue` | ~0.2s（队列操作均在内存中完成） |

## 重要细节
- 使用 `TerminationIdPool` 汇总所有来源的终止 ID，方便后续溯源。
- `test_duplicate_queue_name_raises` 验证了图结构定义的严谨性。

## 注意事项
- 队列机制是 CelestialFlow 异步非阻塞架构的核心支柱。
- 相关实现位于 `src/celestialflow/runtime/core_queue.py`。
