# 耗时预估工具测试 (test_estimators.py)

> 📅 最后更新日期: 2026/05/28

## 作用

验证 `celestialflow.utils.util_estimators` 中的全局任务剩余时间预估函数：`calc_remaining`、`calc_elapsed` 和 `calc_global_remain_equal_pred`。

## 核心测试对象

- `calc_remaining`: 基于 `(pending, processed, elapsed)` 计算单个 Stage 的预估剩余时间。
- `calc_elapsed`: 根据 `time_start`、`time_end` 和 `status` 计算实际已用时间。
- `calc_global_remain_equal_pred`: 遍历全图各节点，根据上游已处理量和下游待处理量，按**等比分布**预估每个节点的剩余时间。

## 关键测试场景

### `TestCalcRemaining`
- 正常推算：`(pending=5, processed=5, elapsed=10)` → 剩余 10s
- 边界值：pending=0、processed=0、三者全为 0 均返回 0
- 浮点数输入支持

### `TestCalcElapsed`
- RUNNING 状态有 pending → 返回 `当前时间 - time_start`
- RUNNING 状态无 pending → 返回 `time_end - time_start`
- STOPPED 状态 → 返回 `time_end - time_start`
- NOT_STARTED → 返回 0
- 连续调用模拟时间推进

### `TestCalcGlobalRemainEqualPred`
- 单节点无前驱 / 全零 pending
- 线性链（三节点 A→B→C）：total_processed 合理分配
- 扇出（一对多）、扇入（多对一）、菱形结构（A→[B,C]→D）
- 瓶颈节点（大 pending 值）
- 结果类型为 `dict[str, float]`，无负数
- 上游无数据但下游有 pending（使用 diff 值）
- 空图处理

### `TestPropertyBased` — 属性测试
- 对称线性链产生相同预估
- 单调性：pending 增大 → 预估增大
- 单调性：processed 增大 → 预估减小

## 运行方式

```bash
# 全部执行
pytest tests/utils/test_estimators.py -v

# 仅运行 calc_remaining 测试
pytest tests/utils/test_estimators.py -k "Remaining" -v

# 仅运行 calc_elapsed 测试
pytest tests/utils/test_estimators.py -k "Elapsed" -v

# 仅运行全局预估测试
pytest tests/utils/test_estimators.py -k "Global" -v

# 仅运行属性测试
pytest tests/utils/test_estimators.py -k "Property" -v
```

## 性能参考

| 测试类 | 耗时 |
|--------|------|
| `TestCalcRemaining` | ~0.01s |
| `TestCalcElapsed` | ~0.02s |
| `TestCalcGlobalRemainEqualPred` | ~0.1s |
| `TestPropertyBased` | ~0.1s |

## 重要细节

- 全局预估使用**等比分布假设**：下游节点的剩余时间按上游各节点已处理量的比例分配。
- 辅助函数 `_make_linear_chain(n)` 构造 n 个节点的线性 DAG，便于快速构建测试拓扑。
- 属性测试（property-based）验证了预估函数的数学单调性，不依赖具体数值。

## 注意事项

- 这些预估函数用于 Dashboard 中的进度估算和 ETA 显示，预估准确性影响用户体验。
- 相关实现位于 `src/celestialflow/utils/util_estimators.py`。
