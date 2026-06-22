# 特化阶段测试 (test_stages.py)

> 📅 最后更新日期: 2026/06/22

## 作用
验证 `celestialflow.stage.core_stages` 中特化任务节点（Splitter, Router）的功能，确保任务能被正确分裂、路由和分发。

## 核心测试对象
- `TaskSplitter`: 将单个任务结果分裂为多个子任务的节点。
- `TaskRouter`: 根据预定义规则将任务导向特定下游节点的路由器。

## 关键测试场景

### `TestTaskSplitter` — 任务分裂器
| 用例 | 覆盖目标 |
|------|----------|
| `test_splitter_init` | 验证默认串行模式、不重试、初始计数器为 0 |
| `test_splitter_process_success` | 在 `TaskGraph` 中成功执行后下游收到 3 个独立任务，`split_counter` 计数正确 |
| `test_splitter_allows_empty_iterable` | 空可迭代输入产生 0 个子任务，不抛异常 |
| `test_splitter_supports_generator_input` | 一次性迭代器（generator）输入仍能正确拆分并分发所有子任务 |
| `test_splitter_allows_constructor_split_item` | 通过 `split_item` 构造函数参数注入单个子任务的转换逻辑 |

### `TestTaskRouter` — 任务路由器
| 用例 | 覆盖目标 |
|------|----------|
| `test_router_init` | 验证默认串行模式、不重试、路由计数器为空字典 |
| `test_router_route_logic` | 验证 `_route` 会调用构造时传入的路由函数，返回 `(target, task)` 结果；未知 target 抛出 `InvalidOptionError` |
| `test_router_process_success` | 在 `TaskGraph` 中成功路由后，`route_counters` 计数正确，目标节点各收到对应数量的成功任务 |
| `test_router_binding_counter_uses_stable_metrics_lock` | 路由计数器从创建起绑定稳定的 metrics 锁，切换 `execution_mode` 后仍保持同一锁对象 |

## 测试重点
- **一对多传播**: 验证 Splitter 的结果列表被展开成多个独立任务信封，而非广播同一结果。
- **具名分发**: 验证 Router 通过内部路由函数和预绑定机制将任务精确导向指定下游节点。
- **状态追踪**: 验证特化节点内部的自定义计数器（`split_counter`, `route_counters`）能准确反映业务逻辑执行情况。

## 运行方式

```bash
# 全部执行
pytest tests/stage/test_stages.py -v

# 仅运行 TaskSplitter 测试
pytest tests/stage/test_stages.py -k "splitter" -v

# 仅运行 TaskRouter 测试
pytest tests/stage/test_stages.py -k "router" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskSplitter` | ~0.2s |
| `TestTaskRouter` | ~0.2s |

## 重要细节
- 测试使用 `TaskGraph.connect()` 和 `TaskGraph.start_graph()` 构建真实的图执行环境进行验证，而非使用 mock 队列截获输出。
- 内置的 `split_counter` 和 `route_counters` 通过特化 Stage 的内部机制自动维护。

## 注意事项
- 特化阶段常用于复杂工作流中的数据分流与并行度动态调整。
- 相关实现位于 `src/celestialflow/stage/core_stages.py`。
