# 具体节点类测试 (test_nodes.py)

> 📅 最后更新日期: 2026/09/10

## 作用

验证 `celestialflow.node.core_nodes` 中三个具体节点类 `TaskExecutor` / `TaskSplitter` / `TaskRouter` 的执行、拆分、路由行为，覆盖串行 / 线程 / 异步三种执行模式、重复检查默认值的 Web 兼容语义、从 sqlite 持久化回放、节点初始化约束以及路由计数器的稳定锁。

## 核心测试对象

| 类 / 函数 | 角色 | 说明 |
|-----------|------|------|
| `TaskExecutor` | 被测类 | 通用执行器，验证 `serial` / `thread` / `async`、异常处理、retry、duplicate、restore_db |
| `TaskSplitter` | 被测类 | 1→N 拆分器，验证 `split_counter`、空可迭代、生成器、自定义 `split_item` |
| `TaskRouter` | 被测类 | 路由器，验证 `route_counters`、未知 target 抛 `InvalidOptionError`、稳定锁 |
| `append_records` | 工具 | 通过 `celestialflow.persistence.util_sqlite` 直接写入失败 / pending 记录用于回放测试 |
| `build_result_dict` | 工具 | 聚合 `get_success_pairs` 与 `get_error_pairs` 为 `{task: result_or_error_str}` |

## 关键测试场景

### `TestTaskExecutor` — 执行器（17 用例）

| 用例 | 覆盖目标 |
|------|---------|
| `test_serial_basic` | 串行执行 5 个任务，succeeded=5、failed=0、pending=0 |
| `test_serial_with_errors` | 串行执行 `[1,-1,2,-2,3]`，`PersistedError.error_type == "ValueError"`，succeeded=3 / failed=2 |
| `test_serial_retry` | 注册 `RuntimeError` 为可重试；前 2 次抛错后第 3 次返回 `x+100`，`call_count == 3` |
| `test_serial_no_retry_for_unmatched_exception` | 未注册的可重试异常不会触发重试，直接 failed |
| `test_thread_basic` | 线程模式（4 worker）成功处理 5 任务 |
| `test_async_basic` | 异步模式成功处理 3 任务 |
| `test_async_double` | 异步模式连续处理 20 任务 |
| `test_duplicate_check_disabled_by_default` | **回归**：`enable_duplicate_check` 默认 `False`，重复任务不计数 |
| `test_duplicate_check_enabled` | 显式开启时 succeeded=3 / duplicated=3 |
| `test_duplicate_check_disabled` | 显式关闭时 succeeded=6 / duplicated=0 |
| `test_restore_db` | 默认只读本节点 `stage == self.get_name()` 的 failed / pending，回放 3 条成功 |
| `test_restore_db_filters_error_type_when_enabled` | `filter_by_error_type=True` + `set_retry_exceptions(RuntimeError)` 时只回放 RuntimeError |
| `test_restore_db_filter_keeps_pending_records` | 开启过滤时 `pending` 记录始终保留 |
| `test_success_persist` | 成功结果写入 `LifecycleSpout` 缓存，`get_success_pairs()` 能读回 |
| `test_rejects_zero_argument_func` | 0 参函数应抛 `ConfigurationError` |
| `test_rejects_multi_argument_func` | 多参函数应抛 `ConfigurationError` |
| `test_name_and_execution_mode` | `get_name()` 与 `execution_mode` 暴露正确 |

### `TestTaskSplitter` — 拆分器（5 用例）

| 用例 | 覆盖目标 |
|------|---------|
| `test_splitter_init` | 默认 `execution_mode="serial"`、`max_retries=0`、`split_counter.get() == 0` |
| `test_splitter_process_success` | `TaskGraph` 串联后下游 `tasks_succeeded == 3`、`split_counter == 3` |
| `test_splitter_allows_empty_iterable` | 空可迭代不抛异常，下游 succeeded=0、split_counter=0 |
| `test_splitter_supports_generator_input` | 一次性生成器也能被完整拆分（split_counter=3） |
| `test_splitter_allows_constructor_split_item` | 构造参数 `split_item=lambda item: item.strip()`，`_split([" a ", " b ", " c "]) == ("a", "b", "c")` |

### `TestTaskRouter` — 路由器（4 用例）

| 用例 | 覆盖目标 |
|------|---------|
| `test_router_init` | 默认 `serial` / `max_retries=0` / `route_counters == {}` |
| `test_router_route_logic` | `_route` 返回 `(target, task)`；未注册 target 抛 `InvalidOptionError` |
| `test_router_process_success` | `TaskGraph` 中两个下游 `target1` / `target2` 各收 1 条，`route_counters` 各自 = 1 |
| `test_router_binding_counter_uses_stable_metrics_lock` | 路由计数器从创建就绑定 `metrics.lock`，切换 `execution_mode` 后锁对象不变 |

## 关键数据流

```mermaid
flowchart LR
    subgraph "TaskExecutor"
        PutTask[put_task] -->|envelope| Q[TaskInQueue]
        Q --> D[Dispatch]
        D --> W[worker]
        W -->|success| SP[process_task_success]
        SP --> Counter[success_counter]
        SP --> Downstream[(下游节点)]
    end

    subgraph "TaskSplitter"
        Q2[TaskInQueue] --> DS[_split]
        DS --> PSR[process_task_success]
        PSR -->|list result| PSR_put[_put_split_result]
        PSR_put --> SC[split_counter]
        PSR_put --> Down2[(下游节点 per item)]
    end

    subgraph "TaskRouter"
        Q3[TaskInQueue] --> DR[_route]
        DR -->|target,task| PR[process_task_success]
        PR --> RC[route_counters target]
        PR --> Down3[(指定下游节点)]
    end
```

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestTaskExecutor` | 17 | 三种执行模式、retry 命中/不命中、duplicate 默认值、sqlite 回放（含按 error_type 过滤）、持久化、回调签名校验 |
| `TestTaskSplitter` | 5 | 默认参数、图集成、空可迭代、生成器、自定义 `split_item` |
| `TestTaskRouter` | 4 | 默认参数、`_route` 拒绝未知 target、图集成、稳定锁 |
| **合计** | **26** | |

## 运行方式

```bash
# 全部执行
pytest tests/node/test_nodes.py -v

# 仅运行 TaskExecutor 测试
pytest tests/node/test_nodes.py -k "TaskExecutor" -v

# 仅运行 TaskSplitter 测试
pytest tests/node/test_nodes.py -k "TaskSplitter" -v

# 仅运行 TaskRouter 测试
pytest tests/node/test_nodes.py -k "TaskRouter" -v

# 仅运行重复检查相关用例
pytest tests/node/test_nodes.py -k "duplicate" -v

# 仅运行 sqlite 回放用例
pytest tests/node/test_nodes.py -k "restore_db" -v
```

## 性能参考

| 测试类 | 耗时 |
|--------|------|
| `TestTaskExecutor` | < 2.0s（含 sqlite 持久化与回放） |
| `TestTaskSplitter` | < 1.0s |
| `TestTaskRouter` | < 1.0s |

## 注意事项

- `test_duplicate_check_disabled_by_default` 是回归测试，确保 `enable_duplicate_check` 默认 `False`，从而降低哈希开销并支持 Web 端重试语义。
- `test_restore_db*` 用例通过 `append_records` 直接写入 sqlite，验证 `load_tasks_grouped_by_stage` 的回放逻辑；记录中的 `stage` 字段为节点名称（与 `TaskGraph` 中 `set_nodes` 一致）。
- `test_router_binding_counter_uses_stable_metrics_lock` 是回归测试，覆盖 `route_counters` 之前在不同模式下因 `TaskMetrics` 重建而失去锁引用的问题；现版本统一使用 `metrics.lock` 锁。
- 异步用例需 `pytest-asyncio` 插件（项目已配置 `pytest.mark.asyncio`）。
- 持久化相关用例依赖全局 `LifecycleSpout` / `LogSpout`；如需隔离，建议在自定义 fixture 中显式 `start()` / `stop()`。
- 相关实现位于 `src/celestialflow/node/core_nodes.py`。
