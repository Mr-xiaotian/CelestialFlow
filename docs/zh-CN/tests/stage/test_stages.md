# 特化阶段测试 (test_stages.py)

> 最后更新日期: 2026/05/23

## 作用
验证 `celestialflow.stage.core_stages` 中特化任务节点（Splitter, Router）的功能，确保任务能被正确分裂、路由和分发。

## 核心测试对象
- `TaskSplitter`: 将单个任务结果分裂为多个子任务的节点。
- `TaskRouter`: 根据预定义规则将任务导向特定下游节点的路由器。

## 关键测试流程
1. **TaskSplitter (任务分裂器)**:
   - **初始化**: 验证默认处于串行模式且不重试。
   - **分裂逻辑**: 模拟执行成功后返回列表 `[1, 2, 3]`，验证输出队列中产生 3 个独立的任务信封，且 `split_counter` 计数正确。
2. **TaskRouter (任务路由器)**:
   - **路由规则**: 验证 `_route` 方法能正确处理 `(target, data)` 元组，提取目标名和数据负载。
   - **分发验证**: 验证任务能准确进入对应的下游具名队列（如 `target1` 的任务只进 `q_target1`），且对应的路由计数器增加。
   - **异常处理**: 验证格式错误（非元组）或目标未知时抛出 `TaskFormatError` 或 `InvalidOptionError`。

## 测试重点
- **一对多传播**: 验证 Splitter 的输出是广播模式还是分裂模式（Splitter 产生新信封）。
- **具名分发**: 验证 Router 能通过 `TaskOutQueue` 的具名发送能力实现精确导航。
- **状态追踪**: 验证特化节点内部的自定义计数器（`split_counter`, `route_counters`）能准确反映业务逻辑执行情况。

## 运行方式

```bash
# 全部执行
pytest tests/stage/test_stages.py -v

# 仅运行 TaskSplitter 测试
pytest tests/stage/test_stages.py -k "splitter" -v
pytest tests/stage/test_stages.py -k "Splitter" -v

# 仅运行 TaskRouter 测试
pytest tests/stage/test_stages.py -k "router" -v
pytest tests/stage/test_stages.py -k "Router" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestSplitter` | ~0.2s |
| `TestRouter` | ~0.2s |

## 重要细节
- 测试中使用 `TaskOutQueue` 的 Mock 配置来截获输出结果进行验证。
- 依赖于 `log_inlet` fixture 进行异步错误日志记录。

## 注意事项
- 特化阶段常用于复杂工作流中的数据分流与并行度动态调整。
- 相关实现位于 `src/celestialflow/stage/core_stages.py`。
