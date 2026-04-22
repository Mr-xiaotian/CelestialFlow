# test_metrics.py 测试说明

> 📅 最后更新日期: 2026/04/22

## 测试目标

验证 `TaskMetrics` 任务指标统计类的所有计数器逻辑、去重机制、重试异常配置及状态判断。`TaskMetrics` 是框架内任务状态可视化和监控的数据源，其计数准确性直接影响运维判断。

## 测试范围

| 测试类 | 用例数 | 覆盖点 |
|--------|--------|--------|
| `TestTaskMetricsBasic` | 8 | 初始值、各计数器、processed/pending 公式、is_finished、reset |
| `TestTaskMetricsDuplicate` | 3 | 去重开关、重复检测、reset_state 清空 |
| `TestTaskMetricsRetryExceptions` | 2 | 默认空异常、动态添加 |

### 关键用例详解

#### `test_processed_equals_sum`
- **目标**：验证核心会计公式：`processed = succeeded + failed + duplicated`；`pending = input - processed`。
- **输入**：10 个任务，5 成功、2 失败、1 重复
- **断言**：`processed == 8`，`pending == 2`

#### `test_is_tasks_finished_true / false`
- **目标**：验证 `is_tasks_finished()` 通过比较 `task_counter` 与 `success + error + duplicate` 判断完成状态。
- **边界**：相等时返回 `True`，不等时返回 `False`。

#### `test_duplicate_check_enabled_detects_repeat`
- **目标**：启用去重后，同一 hash 第二次出现返回 `True`。
- **机制**：内部使用 `set[str]` 存储已处理的 `task_hash`。

#### `test_duplicate_check_resets_with_reset_state`
- **目标**：`reset_state()` 清空 `processed_set`，使已去重的任务可重新进入。
- **注意**：`reset_counter()` 只重置计数器数值，**不**重置去重集合；`reset_state()` 才重置去重集合。

## 依赖

| 依赖 | 说明 |
|------|------|
| `pytest` | 测试框架 |
| `celestialflow.runtime.core_metrics.TaskMetrics` | 被测对象 |

## 可能的问题与注意事项

### 1. 线程/进程安全（当前测试未覆盖）
`TaskMetrics` 内部根据 `execution_mode` 选择不同的计数器实现：
- `serial`：`ValueWrapper`（无锁）
- `thread`：`ValueWrapper` + `threading.Lock`
- `process`：`multiprocessing.Value`

当前单元测试仅在 `serial` 模式下运行，未覆盖并发场景下的计数竞争。若需验证线程安全，应补充以下测试：
```python
def test_thread_safe_counter():
    metrics = TaskMetrics(execution_mode="thread")
    # 多线程并发 add_success_count
```

### 2. `reset_counter` 与 `reset_state` 的职责分离
| 方法 | 重置内容 |
|------|----------|
| `reset_counter()` | `task_counter`、`success_counter`、`error_counter`、`duplicate_counter` 的数值 |
| `reset_state()` | `processed_set`（去重集合） |

常见误区：调用 `reset_counter()` 后期望去重集合也被清空。**实际不会**，需显式调用 `reset_state()`。

### 3. `add_task_count` 与 `task_counter` 的语义
`add_task_count(5)` 是向 `task_counter` 累加初始值。在 `SumCounter` 模式下，这个值可能来自多个子计数器的累加（如 `TaskSplitter` 的拆分计数）。直接修改 `task_counter.value` 可能破坏一致性。

### 4. `is_tasks_finished` 的时序问题
`is_tasks_finished()` 是非阻塞的读取操作。在 `thread` 模式下，如果 worker 线程正在执行 `add_success_count()` 和 `add_task_count()` 之间，可能读到短暂的中间状态（`processed > input` 或 `processed < input`）。

**建议**：在 staged 调度模式下，仅在层间检查此状态，避免在任务执行高峰期调用。

### 5. 重试异常的元组不可变性
`retry_exceptions` 是 `tuple[type[Exception], ...]` 类型，通过 `+` 运算追加。这保证了多线程读取时的一致性，但添加操作不是原子的（虽然当前实现中不影响，因为通常只在初始化阶段配置）。

## 运行方式

```bash
pytest tests/test_metrics.py -v
```

所有用例均为纯内存操作，执行时间 `< 100ms`。

## 相关文件

- `src/celestialflow/runtime/core_metrics.py`：被测实现
- `src/celestialflow/runtime/util_factories.py`：计数器工厂（`make_counter`、`SumCounter`）
- `tests/test_executor.py`：在端到端场景下验证 metrics 计数
