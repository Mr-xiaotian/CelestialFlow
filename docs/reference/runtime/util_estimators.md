# RuntimeEstimators

`runtime/util_estimators.py` 提供运行时耗时估算函数。

## 主要函数

- `calc_remaining(processed, pending, elapsed)`：估算节点剩余时间。
- `calc_elapsed(status, last_elapsed, last_pending, interval)`：按状态累计耗时。
- `calc_global_remain_equal_pred(...)`：基于 DAG 与观测指标估算全局剩余时间。

## 用途

- 驱动监控面板 ETA 展示。
- 辅助识别潜在拥塞节点。
