# test_executor.py 测试说明

> 📅 最后更新日期: 2026/05/08

## 测试目标

验证 `TaskExecutor` 在三种执行模式（`serial` / `thread` / `async`）下的核心能力：任务调度、结果正确性、异常处理、重试机制、去重检查、成功缓存、配置校验及 Observer 回调。`TaskExecutor` 是 CelestialFlow 最基础的任务执行单元，其稳定性是整个框架的基石。

## 测试范围

| 测试类 | 用例数 | 覆盖点 |
|--------|--------|--------|
| `TestExecutorSerial` | 4 | 串行模式基本功能、错误处理、重试、异常过滤 |
| `TestExecutorThread` | 1 | 线程模式并发正确性 |
| `TestExecutorAsync` | 2 | 异步模式基本功能、并发批量任务 |
| `TestExecutorDuplicateCheck` | 2 | 去重启用/禁用 |
| `TestExecutorSuccessCache` | 1 | 成功结果缓存 |
| `TestExecutorConfig` | 2 | 非法配置拦截、summary 字段完整性 |
| `TestExecutorObserver` | 7 | 生命周期回调、错误回调、无 observer、多 observer、移除 observer、CallbackObserver、部分回调 |

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

#### `test_observer_lifecycle`
- **目标**：验证 observer 在执行过程中收到完整生命周期回调（start → success × N → finish）。
- **设计**：`RecordingObserver` 记录所有事件，验证事件类型和顺序。

#### `test_callback_observer`
- **目标**：验证 `CallbackObserver` 通过回调函数接收事件。
- **设计**：传入 `on_task_success` 和 `on_finish` 回调，验证调用次数。

#### `test_multiple_observers`
- **目标**：验证多个 observer 同时收到回调。

#### `test_remove_observer`
- **目标**：验证移除 observer 后不再收到回调。

## 依赖

| 依赖 | 说明 |
|------|------|
| `pytest` | 测试框架 |
| `pytest-asyncio` | 异步测试支持 |
| `celestialflow.TaskExecutor` | 被测对象 |
| `celestialflow.BaseObserver` | Observer 基类 |
| `celestialflow.CallbackObserver` | 回调式 Observer |

## 运行方式

```bash
# 全部执行
pytest tests/test_executor.py -v

# 仅串行测试
pytest tests/test_executor.py::TestExecutorSerial -v

# 仅 Observer 测试
pytest tests/test_executor.py::TestExecutorObserver -v
```

## 相关文件

- `src/celestialflow/stage/core_executor.py`：被测实现
- `src/celestialflow/runtime/core_dispatch.py`：调度逻辑
- `src/celestialflow/observability/core_observer.py`：Observer 基类
- `demo/demo_executor.py`：TaskExecutor 的演示脚本
