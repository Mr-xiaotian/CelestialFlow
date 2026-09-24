# tests/runtime/test_metrics.py

> 📅 最后更新日期: 2026/09/24

## 作用
验证 `celestialflow.runtime.core_metrics` 中的 `TaskMetrics` 类，确保任务执行过程中的各项统计指标（输入、成功、失败、重复、待处理）计算准确，并覆盖上游/下游绑定计数器、可重试异常配置与忙碌墙钟耗时（busy time）的累计口径。

## 核心测试对象
- `TaskMetrics`: 负责单个节点（Stage）的任务计数、上下游绑定计数、可重试异常与忙碌耗时追踪。
- `ValueWrapper`: 用于上下游计数的线程安全包装器，测试中直接以 `ValueWrapper` 模拟上游/下游计数器。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestTaskMetricsBasic` | 9 | 初始计数、外部输入累加、外部/上游输入拆分、成功/失败/重复累加、`processed`/`pending` 公式、完成判定 |
| `TestTaskMetricsBinding` | 5 | 上游计数器计入总数、`connect_to` 共享计数器、未注册下游抛 `KeyError`、上下游计数映射查询 |
| `TestTaskMetricsRetryExceptions` | 2 | 默认可重试异常为空、动态添加异常类型 |
| `TestTaskMetricsElapsed` | 3 | 忙碌耗时初始为 0、仅在执行期间累积、并发重叠按墙钟计一次 |
| **合计** | **19** | |

## 关键测试场景

### 基础计数 (`TestTaskMetricsBasic`)
1. **初始状态** (`test_initial_counts`): 新建 `TaskMetrics` 时 `tasks_input/succeeded/failed/duplicated/processed/pending` 均为 0，`get_external_input_count()`、`get_upstream_input_count()` 为 0，上下游计数映射为空字典。
2. **外部输入累加** (`test_add_external_input_count`): `add_external_input_count(5)` 后外部输入为 5、上游输入为 0、`get_input_count()` 与 `tasks_input` 均为 5。
3. **输入拆分** (`test_input_count_split_external_and_upstream`): 通过 `set_upstream_counter` 注册两个上游，分别累加后验证外部 3、上游 6、合计 9。
4. **成功/失败/重复累加**: `add_success_count`、`add_fail_count`、`add_duplicate_count` 分别更新对应 Getter 与 `get_counts()` 键。
5. **公式验证** (`test_processed_equals_sum`): 验证 `tasks_processed = succeeded + failed + duplicated`，`tasks_pending = input - processed`。
6. **完成判定** (`test_is_tasks_finished_true` / `_false`): `pending` 为 0 时返回 `True`，否则返回 `False`。

### 上下游绑定 (`TestTaskMetricsBinding`)
- `test_upstream_counter_adds_to_task_count`: 上游 `ValueWrapper` 增加 3 后，当前节点的 `get_input_count()` 与 `get_upstream_input_count()` 均为 3，外部输入为 0。
- `test_shared_binding_counter`: `prev.set_downstream_counter` 与 `curr.set_upstream_counter` 传入同一 `ValueWrapper`，`prev.add_downstream_count` 后 `curr.get_input_count()` 反映该增量。
- `test_add_downstream_count_missing_target_raises`: 对未注册名称调用 `add_downstream_count` 抛出 `KeyError`。
- `test_get_upstream_counts` / `test_get_downstream_counts`: 验证返回 `{名称: 数量}` 映射。

### 重试配置 (`TestTaskMetricsRetryExceptions`)
- 默认 `retry_exceptions == ()`。
- `set_retry_exceptions(ValueError, RuntimeError)` 后两种异常均出现在 `retry_exceptions` 元组中。

### 忙碌耗时 (`TestTaskMetricsElapsed`)
使用可手动推进的 `_FakeClock` 替身 `celestialflow.runtime.core_metrics.time.perf_counter`：
1. **初始为 0** (`test_elapsed_is_zero_without_tasks`): 无任务执行时 `get_elapsed() == 0.0`。
2. **仅忙碌期间累积** (`test_elapsed_accumulates_only_while_busy`): `begin_task()` 后未闭合的时间片也计入（2.0s）；`end_task()` 后空闲 5s 不再增加。
3. **并发重叠计一次** (`test_elapsed_counts_overlapping_tasks_once`): 两次 `begin_task()` 重叠期间按墙钟计一次，各任务时长之和为 5s 时只记 3s；结束后空闲不再增加。

## 测试重点
- **指标守恒**: `tasks_input` 与 `tasks_processed + tasks_pending` 保持一致。
- **绑定共享**: 上下游通过同一 `ValueWrapper` 实例共享计数，`connect_to` 语义由此保证。
- **耗时口径**: 忙碌耗时按节点墙钟时间累计，并发任务重叠区间只计一次。

## 运行方式

```bash
# 全部执行
pytest tests/runtime/test_metrics.py -v

# 仅运行基础计数测试
pytest tests/runtime/test_metrics.py -k "count" -v

# 仅运行上下游绑定测试
pytest tests/runtime/test_metrics.py -k "binding or upstream or downstream" -v

# 仅运行忙碌耗时测试
pytest tests/runtime/test_metrics.py -k "elapsed" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskMetricsBasic` / `TestTaskMetricsBinding` / `TestTaskMetricsRetryExceptions` | ~0.1s（纯逻辑运算） |
| `TestTaskMetricsElapsed` | < 0.1s（假时钟替身，无真实等待） |

## 重要细节
- 统计指标是 Dashboard 展示和图运行终止判定的数据来源。
- `get_elapsed()` 在 `_busy_since` 非空时会把当前未闭合的时间片一并计入。
- `_FakeClock` 通过 `monkeypatch.setattr` 替换 `core_metrics.time.perf_counter`，测试不产生真实等待。

## 注意事项
- 统计指标的准确性直接影响 `TaskGraph` 的自动关闭判定。
- 相关实现位于 `src/celestialflow/runtime/core_metrics.py`。
