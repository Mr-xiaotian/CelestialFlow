# bench_tqdm.py 基准测试说明

## 目标

量化 `tqdm` 进度条在循环中的性能开销，帮助判断在超大规模迭代（数百万级）中是否应启用进度显示。

## 测试内容

- **有 tqdm**：每轮迭代调用 `pbar.update(1)`
- **无 tqdm**：裸循环
- **数据规模**：默认 `data_size = 1_000_000`
- **模拟处理**：`item * 2`（极轻量级运算）

## 关键参数

- `dynamic_ncols=True`：自动适应终端宽度
- `total=0` 后动态设置 `pbar.total = len(data)`：演示延迟设置总量的用法

## 可能出现的问题

1. **TTY 检测开销**：若输出被重定向到文件或管道，`tqdm` 可能自动禁用显示，但仍会执行部分刷新逻辑，导致与直接终端运行结果不一致。
2. **`dynamic_ncols` 的终端查询**：每次刷新都会查询终端宽度，在某些 CI 环境或 Windows PowerShell 中可能触发缓慢的系统调用。
3. **大循环中的内存增长**：测试代码将 `range(data_size)` 完整展开为 `list` 存入 `data`，当 `data_size` 提升到 1000 万时，仅列表本身就占用约 80MB 内存。

## 运行方式

```bash
python bench/bench_tqdm.py
```

## 依赖

- `tqdm`
