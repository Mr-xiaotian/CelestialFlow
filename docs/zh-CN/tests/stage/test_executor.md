# 任务执行器测试 (test_executor.py)

> 最后更新日期: 2026/06/11

## 作用
验证 `celestialflow.stage.core_executor` 中的 `TaskExecutor` 类，确保其在各种并发模式下能准确执行任务、处理错误并支持高级特性（如重试和去重）。

## 核心测试对象
- `TaskExecutor`: 执行单个任务逻辑的底层引擎。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestExecutorSerial` | 4 | 串行执行、错误处理、重试成功、非匹配异常不重试 |
| `TestExecutorThread` | 1 | 线程池并行执行与正确计数 |
| `TestExecutorAsync` | 2 | 异步执行与连续处理逻辑 |
| `TestExecutorDuplicateCheck` | 2 | 去重启用/禁用的行为对比 |
| `TestExecutorReplay` | 1 | `start_db` 从 sqlite 按 stage 读取失败任务并回放 |
| `TestExecutorSuccessCache` | 1 | 成功结果缓存与 `get_success_pairs()` |
| `TestExecutorConfig` | 4 | 零/多参数函数拒绝、非法执行模式校验、`get_summary()` 摘要信息 |

## 关键测试场景

### 执行模式
- **Serial**: 顺序执行，验证结果映射和计数。
- **Thread**: 并行执行，验证多线程下的任务分发（`execution_mode="thread"`）。
- **Async**: 异步执行，验证 `start_async` 的协程处理（`execution_mode="async"`）。

### 重试机制
- 验证 `max_retries` 逻辑：只有在指定的 `retry_exceptions` 抛出时才触发重试。
- 验证重试成功后，最终计数标记为成功而非失败。
- 验证非匹配异常（如配置重试 `RuntimeError` 但抛出 `ValueError`）能立即触发失败。

### 去重与缓存
- 验证 `enable_duplicate_check` 开启时，相同任务仅执行一次，重复计入 `tasks_duplicated`。
- 验证 `enable_duplicate_check` 关闭时，相同任务全部执行，`tasks_duplicated` 为 0。
- 验证 `get_success_pairs()` 能正确返回已成功任务的输入输出配对。

### 配置校验
- 验证非法 `execution_mode` 在初始化时抛出 `ExecutionModeError`。
- 验证 `get_summary()` 返回 `name`、`func_name`、`execution_mode` 等关键字段。

## 测试重点
- **执行模式一致性**: 确保无论使用何种执行模式，最终的任务计数和结果收集逻辑保持一致。
- **重试精度**: 验证非匹配异常能立即触发失败。
- **并发安全性**: 验证线程池和异步模式下的结果收集不会出现竞争或丢失。

## 运行方式

```bash
# 全部执行
pytest tests/stage/test_executor.py -v

# 仅运行 Serial 模式测试
pytest tests/stage/test_executor.py -k "serial" -v

# 仅运行 Thread 模式测试
pytest tests/stage/test_executor.py -k "thread" -v

# 仅运行 Async 模式测试
pytest tests/stage/test_executor.py -k "async" -v

# 仅运行重试机制测试
pytest tests/stage/test_executor.py -k "retry" -v

# 仅运行去重测试
pytest tests/stage/test_executor.py -k "duplicate" -v
```

## 性能参考

| 测试类 | 耗时 |
|------|------|
| `TestExecutorSerial` | ~1s |
| `TestExecutorThread` | ~1s |
| `TestExecutorAsync` | ~2s |
| `TestExecutorDuplicateCheck` / `TestExecutorSuccessCache` / `TestExecutorConfig` | < 0.5s |

## 重要细节
- 使用 `flaky` 闭包模拟需要重试的场景。
- `test_invalid_execution_mode` 确保不支持的模式在初始化时即报错。

## 注意事项
- `TaskExecutor` 是 `TaskStage` 的核心组件，负责具体的函数调用逻辑。
- 相关实现位于 `src/celestialflow/stage/core_executor.py`。
