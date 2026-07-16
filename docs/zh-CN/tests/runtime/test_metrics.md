# 任务指标测试 (test_metrics.py)

> 📅 最后更新日期: 2026/07/16

## 作用
验证 `celestialflow.runtime.core_metrics` 中的 `TaskMetrics` 类，确保任务执行过程中的各项统计指标（成功、失败、重复、待处理等）计算准确。

## 核心测试对象
- `TaskMetrics`: 负责单个阶段（Stage）或全局的任务计数与状态追踪。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestTaskMetricsBasic` | 9 | 初始状态、基础计数累加、公式验证、完成判定、计数器重置 |
| `TestTaskMetricsDuplicate` | 3 | 去重启用/禁用、`reset_state()` 清空哈希集 |
| `TestTaskMetricsRetryExceptions` | 2 | 默认可重试异常为空、动态添加异常类型 |

## 关键测试场景
1. **基础计数**: 验证 `add_task_count`, `add_success_count`, `add_error_count`, `add_duplicate_count` 等方法的累加逻辑。
2. **公式验证**: 验证 `tasks_processed = tasks_succeeded + tasks_failed + tasks_duplicated`，以及 `tasks_pending = tasks_input - tasks_processed`。
3. **状态判定**: 验证 `is_tasks_finished()` 在不同计数组合下的返回结果（Pending 为 0 时为 True）。
4. **去重逻辑**:
   - 验证去重功能禁用时，相同哈希始终返回 `False`。
   - 验证去重功能启用时，相同哈希的二次检查返回 `True`。
   - 验证 `reset_state()` 能清空哈希集合，允许相同任务再次通过。
5. **重试配置**: 验证动态添加可重试异常类型的逻辑。

## 测试重点
- **指标守恒**: 确保 `tasks_input` 与 `tasks_processed + tasks_pending` 始终保持一致。
- **去重准确性**: 验证哈希集合能有效识别重复任务，防止冗余计算。
- **重置功能**: 验证 `reset_counter()`（仅重置数值）与 `reset_state()`（重置数值及去重集合）的区别。

## 运行方式

```bash
# 全部执行
pytest tests/runtime/test_metrics.py -v

# 仅运行基础计数测试
pytest tests/runtime/test_metrics.py -k "count" -v

# 仅运行去重逻辑测试
pytest tests/runtime/test_metrics.py -k "duplicate" -v

# 仅运行重置功能测试
pytest tests/runtime/test_metrics.py -k "reset" -v

# 仅运行重试配置测试
pytest tests/runtime/test_metrics.py -k "retry" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskMetricsBasic` / `TestTaskMetricsDuplicate` / `TestTaskMetricsRetryExceptions` | ~0.1s（纯逻辑运算） |

## 重要细节
- 统计指标是 Dashboard 展示和图运行终止判定的数据来源。

## 注意事项
- 统计指标的准确性直接影响 `TaskGraph` 的自动关闭判定。
- 相关实现位于 `src/celestialflow/runtime/core_metrics.py`。
