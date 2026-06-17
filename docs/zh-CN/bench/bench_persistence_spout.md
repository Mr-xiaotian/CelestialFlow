# bench_persistence_spout.py 基准测试说明

> 📅 最后更新日期: 2026/06/17

## 目标

评估持久化相关 `spout` 在“队列已预填充大量记录、只测后台消费与写入”场景下的吞吐上限。

本脚本当前覆盖两类目标：

- `LogSpout`
- `FallbackSpout`

其中：

- `LogSpout` 用于测量单线程日志写文件的清队列速度
- `FallbackSpout` 用于测量 SQLite fallback 在“每条有效变更后直接 `commit()`”模式下的事务吞吐

## 测试内容

| 测试项 | 说明 | 计时范围 |
|--------|------|----------|
| `LogSpout` | 预先构造日志记录并压入队列，然后启动 `spout` 清空队列 | `start()` 到 `stop()` |
| `FallbackSpout` | 预先构造 `insert` 记录并压入队列，然后启动 `spout` 清空队列 | `start()` 到 `stop()` |

脚本采用的模型是：

```text
preload queue -> start spout -> drain all queued records
```

因此测试结果更接近“后台写入端的极限处理速度”，不包含调用方实时生产数据的成本。

## 关键配置

- `--log-count`：默认 `200_000`
- `--fallback-count`：默认 `20_000`
- `LogSpout` 输出到临时目录下的 `bench_task_logger.log`
- `FallbackSpout` 输出到临时目录下的 `bench_fallback.sqlite3`
- `FallbackSpout` 使用当前项目实现，即“每条有效变更后直接 `commit()`”

## 可能出现的问题

1. **`LogSpout` 结果不等于真实硬盘强制落盘频率**：当前测试没有为每条记录执行显式 `flush()` 或 `fsync()`，测到的更接近文件缓冲与页缓存写入速度。
2. **`FallbackSpout` 的瓶颈主要在事务提交**：本轮结果很大程度上反映的是 SQLite 在当前磁盘和事务模式下的 `commit()` 吞吐，而不只是 Python 循环开销。
3. **启动和停止成本会影响小样本结果**：当记录数太少时，线程启动、终止信号和收尾 `commit()` 的固定成本会放大。
4. **大样本下可能出现不稳定现象**：本地曾尝试更大样本 `--log-count 500000 --fallback-count 50000`，`LogSpout` 正常完成，但 `FallbackSpout` 阶段出现过一次解释器崩溃，因此建议把该规模视作压力探索值，而不是稳定基线。

## 基准结果（实测）

### 2026/06/17 - Windows 本地首次实测

> 环境：Windows，本地 `.venv`，模型为“预填充队列后启动 spout 清空”，`log-count=200000`，`fallback-count=20000`

| 测试项 | 记录数 | 总耗时 | 吞吐 | 单条平均耗时 |
|--------|--------|--------|------|--------------|
| `LogSpout` | 200,000 | 0.2036s | 982,287.88 records/s | 1.02 us |
| `FallbackSpout` | 20,000 | 3.2515s | 6,151.08 records/s | 162.57 us |

**本轮结论**：

- `LogSpout` 已接近百万条每秒，说明当前实现下日志写入瓶颈主要还不在 Python 侧
- `FallbackSpout` 大约为每秒 6.1k 条，量级明显受 SQLite 单条事务提交限制
- 两者吞吐差距约为 **160x**

### 2026/06/17 - Windows 本地复测（中等放大样本）

> 环境：Windows，本地 `.venv`，模型同上，`log-count=300000`，`fallback-count=30000`

| 测试项 | 记录数 | 总耗时 | 吞吐 | 单条平均耗时 |
|--------|--------|--------|------|--------------|
| `LogSpout` | 300,000 | 0.2960s | 1,013,446.75 records/s | 0.99 us |
| `FallbackSpout` | 30,000 | 4.6633s | 6,433.23 records/s | 155.44 us |

**本轮补充结论**：

- `LogSpout` 在放大样本后仍稳定在约 **100 万条/秒**
- `FallbackSpout` 在放大样本后仍稳定在约 **6.4k 条/秒**
- 当前机器和实现下，`log` 不是瓶颈，`fallback/sqlite` 才是主要限制项

## 运行方式

```bash
python bench/bench_persistence_spout.py
```

若项目未安装为可导入包，也可以直接使用本地虚拟环境解释器：

```bash
.\.venv\Scripts\python.exe bench/bench_persistence_spout.py
```

## 参数调整

### 调整日志样本数

```bash
python bench/bench_persistence_spout.py --log-count 500000
```

### 调整 fallback 样本数

```bash
python bench/bench_persistence_spout.py --fallback-count 50000
```

### 同时调整两类样本

```bash
python bench/bench_persistence_spout.py --log-count 300000 --fallback-count 30000
```

## 依赖

- Python 标准库
- 项目源码中的 `celestialflow.persistence`
