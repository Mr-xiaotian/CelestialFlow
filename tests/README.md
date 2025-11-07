# test_manage.py

本文件用于测试 CelestialFlow 框架中 **TaskManager** 的基本功能与运行模式。

**TaskManager** 是 CelestialFlow 框架中最基础的任务执行单元，在本测试中，它以**独立运行模式（Standalone Mode）**运行，与作为节点被嵌入到 **TaskGraph** 中的“stage 模式”不同。

在独立模式下，TaskManager 自行负责任务调度、异常重试、计数与并发控制，无需依赖图结构即可完成完整的任务生命周期管理。

本测试文件通过递归计算 Fibonacci 数列的示例函数，验证了 TaskManager 在 **单线程（serial）**、**多线程（thread）**、**多进程（process）** 与 **异步（async）** 四种执行模式下的正确性、稳定性与性能表现。

---

### 🔹 `test_manager()`

测试 **TaskManager** 在同步执行环境中的运行行为。

* **任务函数**：`fibonacci(n)`（递归计算第 n 个 Fibonacci 数）
* **运行模式**：单线程、线程池、多进程（通过 `manager.test_methods()` 自动测试三种模式）
* **测试特性**：

  * 输入数据包含非法值（`0`、`None`、空字符串），用于验证异常捕获与重试逻辑；
  * 设置 `max_retries=1`，并允许对 `ValueError` 异常进行重试；
  * 启用进度条显示与日志记录。
* **主要验证点**：

  1. 各执行模式下任务调度与计数逻辑是否一致；
  2. 异常任务能否被正确识别与重试；
  3. `test_methods()` 是否能准确统计不同模式下的执行时间与性能差异。


## 🔹 test_manager_async()
测试 TaskManager 在异步模式下的行为。

- 任务函数：`fibonacci_async(n)`（递归计算的异步版本）
- 执行模式：`async`（协程并发执行）
- 任务特性：
  - 与同步测试相同的数据输入与错误设计；
  - 使用 `await manager.start_async()` 启动任务；
  - 记录整个任务批次的总执行时间。
- 主要验证点：
  1. 异步任务能否在高并发下正确完成；
  2. 异常捕获与重试机制是否在协程环境下正常；
  3. 异步执行相对于同步执行的性能对比。

---

运行方式：
```bash
pytest tests/test_manage.py
```

或单独运行异步测试：

```bash
pytest tests/test_manage.py::test_manager_async
```

