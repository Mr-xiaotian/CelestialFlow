# bench_utils.py 基准测试说明

> 📅 最后更新日期: 2026/04/22

## 目标

为 `bench/` 目录下的各基准测试提供统一的统计输出工具 `summarize()`，标准化耗时数据的呈现格式。

## 功能

```python
def summarize(name: str, durations: list[float], count: int) -> None
```

输出内容：
- 每轮耗时（原始值）
- 平均耗时（mean）
- 标准差（pstdev）
- 吞吐量（`count / mean_s`，items/s）

## 关键实现

- 使用 `statistics.pstdev`（总体标准差），适用于小样本（`REPEAT = 3`）
- 吞吐量计算基于平均值，若各轮次差异大，该值仅供参考

## 可能出现的问题

1. **样本量过小**：多数 benchmark 的 `REPEAT = 3`，`pstdev` 对异常值敏感，若某一轮因系统抖动（如后台进程、垃圾回收）耗时突增，标准差会显著膨胀。
2. **零值保护**：`throughput = count / mean_s if mean_s > 0 else 0.0`，在极快场景下（`mean_s` 接近浮点精度下限）可能产生极大值。

## 运行方式

此文件本身不可直接运行，作为共享模块被导入：
```python
from bench_utils import summarize
```

## 相关文件

- `bench/bench_ipc_queue.py`
- `bench/bench_mpqueue_vs_shared_memory.py`
