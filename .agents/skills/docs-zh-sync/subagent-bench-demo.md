# Subagent: Bench + Demo

> 覆盖 `bench/` 和 `demo/` 目录下所有文件的中文文档。

## 文件清单

### bench (14 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `bench/bench_datastructures.py` | `docs/zh-CN/bench/bench_datastructures.md` |
| 2 | `bench/bench_execution_mode.py` | `docs/zh-CN/bench/bench_execution_mode.md` |
| 3 | `bench/bench_futures_memory.py` | `docs/zh-CN/bench/bench_futures_memory.md` |
| 4 | `bench/bench_graph_mode.py` | `docs/zh-CN/bench/bench_graph_mode.md` |
| 5 | `bench/bench_hash.py` | `docs/zh-CN/bench/bench_hash.md` |
| 6 | `bench/bench_hash_container.py` | `docs/zh-CN/bench/bench_hash_container.md` |
| 7 | `bench/bench_hash_memory.py` | `docs/zh-CN/bench/bench_hash_memory.md` |
| 8 | `bench/bench_http_grpc.py` | `docs/zh-CN/bench/bench_http_grpc.md` |
| 9 | `bench/bench_ipc_queue.py` | `docs/zh-CN/bench/bench_ipc_queue.md` |
| 10 | `bench/bench_mpqueue_vs_shared_memory.py` | `docs/zh-CN/bench/bench_mpqueue_vs_shared_memory.md` |
| 11 | `bench/bench_queue.py` | `docs/zh-CN/bench/bench_queue.md` |
| 12 | `bench/bench_requests.py` | `docs/zh-CN/bench/bench_requests.md` |
| 13 | `bench/bench_tqdm.py` | `docs/zh-CN/bench/bench_tqdm.md` |
| 14 | `bench/bench_utils.py` | `docs/zh-CN/bench/bench_utils.md` |

### demo (6 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `demo/__init__.py` | `docs/zh-CN/demo/__init__.md` |
| 2 | `demo/demo_executor.py` | `docs/zh-CN/demo/demo_executor.md` |
| 3 | `demo/demo_graph.py` | `docs/zh-CN/demo/demo_graph.md` |
| 4 | `demo/demo_stages.py` | `docs/zh-CN/demo/demo_stages.md` |
| 5 | `demo/demo_structure.py` | `docs/zh-CN/demo/demo_structure.md` |
| 6 | `demo/demo_utils.py` | `docs/zh-CN/demo/demo_utils.md` |

## 区域特化陷阱（高频错误）

| 陷阱 | 典型表现 | 排查方法 |
|------|---------|---------|
| 🔴 虚构类/子类 | 文档杜撰了 `DownloadRedisTransport`、`DownloadStage` 等自定义子类，源码中不存在 | grep demo 源码中的 `class ` |
| 🔴 变量名/函数名引用错误 | 文档引用 `hash_methods`/`test_data`/`main()`/`numbers`，实际是 `METHODS`/`TEST_CASES`/`bench_task_1` | grep 源码中的变量定义 |
| 🟠 算法描述错误 | 斐波那契描述为"递归" → 实际迭代 O(n)；声称"serial 模式下 10 秒以上"与迭代实现不符 | 阅读实际算法实现 |
| 🟠 虚构方法调用 | 文档写"调用 `graph.get_graph_summary()`"、"调用 `graph.get_status_snapshot()`"，源码未调用这些方法 | 阅读 demo 脚本的 `main()` 或执行路径 |
| 🟠 参数默认值描述错误 | `data_size` 函数签名默认 `10_000_000`，但文档写的是 `__main__` 调用值 `1_000_000` | 区分函数签名默认值 vs 调用时传入值 |
| 🟡 函数调用名错误 | `run_queue_case` → `run_pipe_case` | grep 函数调用 |
| 🟡 废弃标记过期 | 文档标"已废弃"但实际仍在 `main()` 中默认运行 | 阅读 `__main__` 代码块 |
| 🟡 路径描述错误 | `demo_redis_ack_2` 的路径描述 `download_py/`/`download_go/` 与实际不符 | 阅读实际路径引用 |
| 🟢 实测数据不可验证 | Bench 结果表中的毫秒数（如 `put=0.0008s`）无法从源码验证 | 标注"需人工确认" |

### 区域差异化写作规则

**Bench 文档：**
- 重点说明：**比较对象**、**衡量指标**、**实验目的**、**结论边界**。
- 使用示例应展示如何修改 `N`、`max_workers`、`COUNT` 等参数来调整基准测试规模：
  ```bash
  # 修改 bench_hash.py 中的 TEST_CASES 来调整测试数据
  # 修改 N (重复次数) 来调整统计精度
  python -m bench.bench_hash
  ```
- 用 ```bash 代码块展示运行命令。
- 用**表格**对比不同 benchmark 场景的参数和预期结果。
- 用 `flowchart` 展示 benchmark 的执行流程。
- 不要声称"推荐使用 A 而非 B"，除非代码中明确表达了这一倾向。
- 对于文档中的实测数据（如运行时间），如果无法从源码验证，标注"需人工确认"。

**Demo 文档：**
- 重点说明：**演示目的**、**运行方式**、**预期行为**、**依赖**。
- 使用示例应展示终端输出的 **mock 示例**，帮助用户理解运行后应看到什么：
  ```
  # 预期输出 (mock)
  ========== Demo: Executor Modes ==========
  [SerialExecutor]   Fibonacci(30) = 832040  |  time: 0.0123s
  [ThreadExecutor]   Fibonacci(30) = 832040  |  time: 0.0456s
  ```
- `demo/__init__.md`：新增**演示模块总览表格**，列出全部 demo 模块及各自演示目标。
- 对长时间运行的 demo（如含回环的图结构），标注建议运行时间和终止方式（如 Ctrl+C）。
