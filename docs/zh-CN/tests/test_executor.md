# test_executor.py 测试说明

> 📅 最后更新日期: 2026/04/22

## 测试目标

验证 `TaskExecutor` 在三种执行模式（`serial` / `thread` / `async`）下的核心能力：任务调度、结果正确性、异常处理、重试机制、去重检查、成功缓存及配置校验。`TaskExecutor` 是 CelestialFlow 最基础的任务执行单元，其稳定性是整个框架的基石。

## 测试范围

| 测试类 | 用例数 | 覆盖点 |
|--------|--------|--------|
| `TestExecutorSerial` | 4 | 串行模式基本功能、错误处理、重试、异常过滤 |
| `TestExecutorThread` | 1 | 线程模式并发正确性 |
| `TestExecutorAsync` | 2 | 异步模式基本功能、并发批量任务 |
| `TestExecutorDuplicateCheck` | 2 | 去重启用/禁用 |
| `TestExecutorSuccessCache` | 1 | 成功结果缓存 |
| `TestExecutorConfig` | 2 | 非法配置拦截、summary 字段完整性 |

### 关键用例详解

#### `test_serial_basic`
- **目标**：验证串行模式下任务按顺序执行，结果字典与计数器统计正确。
- **输入**：`[1, 2, 3, 4, 5]`，函数 `add_one`
- **断言**：`result_dict[x] == x + 1`；`tasks_succeeded == 5`

#### `test_serial_with_errors`
- **目标**：验证部分任务失败时，成功任务继续执行，错误信息被正确记录。
- **输入**：`[1, -1, 2, -2, 3]`，函数 `raise_on_negative`
- **断言**：3 个成功，2 个失败；失败结果中包含异常文本。

#### `test_serial_retry`
- **目标**：验证重试机制在配置的异常类型上生效，且最终成功不计入失败。
- **设计**：`flaky` 函数前 2 次调用抛 `RuntimeError`，第 3 次成功。
- **断言**：`call_count == 3`（1 次初始 + 2 次重试）；`tasks_failed == 0`

#### `test_serial_no_retry_for_unmatched_exception`
- **目标**：验证未配置的异常类型不触发重试，直接计入失败。
- **设计**：配置重试 `RuntimeError`，但函数抛 `ValueError`。

#### `test_duplicate_check_enabled`
- **目标**：启用去重后，重复输入仅执行一次。
- **输入**：`[1, 1, 2, 2, 2, 3]`
- **断言**：`tasks_succeeded == 3`，`tasks_duplicated == 3`

## 依赖

| 依赖 | 说明 |
|------|------|
| `pytest` | 测试框架 |
| `pytest-asyncio` | 异步测试支持 |
| `celestialflow.TaskExecutor` | 被测对象 |

## 可能的问题与注意事项

### 1. 线程模式下的结果顺序
`test_thread_basic` 仅验证结果正确性，**不验证执行顺序**。在多线程环境下，任务完成顺序可能与输入顺序不同，若业务逻辑依赖顺序，应在 `process_result()` 中显式处理。

### 2. 异步测试的事件循环策略
`pytest-asyncio` 默认使用 `function` 作用域的事件循环。如果同时运行大量异步测试（>100），可能出现事件循环资源耗尽。当前 2 个异步用例无此风险。

### 3. `process_result_dict` 的键冲突
`process_result_dict()` 使用原始 task 作为字典键。如果 task 是不可哈希类型（如 `list`、`dict`），会抛出 `TypeError`。当前测试使用的均为整数，无此问题。

**建议**：在生产环境中，若任务为不可哈希对象，应自定义 `process_result()` 或使用 `get_success_pairs()`。

### 4. 重试时的闭包状态
`test_serial_retry` 使用 `nonlocal call_count` 追踪调用次数。在 `thread` 模式下，若 `call_count` 未使用线程安全机制（如 `threading.Lock`），可能导致计数竞争。当前串行测试无此问题，但若将 `flaky` 用于 `thread` 模式，需改用 `Value` 或 `Lock`。

### 5. `show_progress=False` 的必要性
所有测试用例均显式设置 `show_progress=False`。若遗漏此参数，在 CI/CD 无 TTY 环境中可能导致 `tqdm` 输出乱码或阻塞。

### 6. 非法模式测试的异常类型
`test_invalid_execution_mode` 使用 `pytest.raises(Exception)` 而非精确异常类型。虽然当前实现抛出 `ExecutionModeError`，但测试写得较宽松。建议改为：
```python
with pytest.raises(ExecutionModeError):
    ...
```

## 运行方式

```bash
# 全部执行
pytest tests/test_executor.py -v

# 仅串行测试
pytest tests/test_executor.py::TestExecutorSerial -v

# 仅异步测试
pytest tests/test_executor.py::TestExecutorAsync -v
```

## 性能参考

在普通开发机上：
- 串行 5 个任务：`< 10ms`
- 线程 5 个任务：`< 20ms`
- 异步 20 个任务：`< 10ms`

## 相关文件

- `src/celestialflow/stage/core_executor.py`：被测实现
- `src/celestialflow/runtime/core_dispatch.py`：调度逻辑
- `tests/demo_executor.py`：TaskExecutor 的演示/集成测试（无断言）
