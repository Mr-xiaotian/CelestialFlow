# 任务执行器测试 (test_executor.py)

> 最后更新日期: 2026/05/23

## 作用
验证 `celestialflow.stage.core_executor` 中的 `TaskExecutor` 类，确保其在各种并发模式下能准确执行任务、处理错误并支持高级特性（如重试和去重）。

## 核心测试对象
- `TaskExecutor`: 执行单个任务逻辑的底层引擎。

## 关键测试流程
1. **模式验证**:
   - **Serial**: 顺序执行，验证结果映射和计数。
   - **Thread**: 并行执行，验证多线程下的任务分发。
   - **Async**: 异步执行，验证 `start_async` 的协程处理。
2. **重试机制**:
   - 验证 `max_retries` 逻辑：只有在指定的 `retry_exceptions` 抛出时才触发重试。
   - 验证重试成功后，最终计数标记为成功而非失败。
3. **去重与缓存**:
   - 验证 `enable_duplicate_check` 开启时，相同任务仅执行一次。
   - 验证 `get_success_pairs()` 能正确返回已成功任务的输入输出配对。
4. **错误记录**: 验证失败任务的错误类型、错误消息以及所属阶段被准确记录到 `get_error_pairs()`。

## 测试重点
- **执行模式一致性**: 确保无论使用何种执行模式，最终的任务计数和结果收集逻辑保持一致。
- **重试精度**: 验证非匹配异常（如配置重试 RuntimeError 但抛出 ValueError）能立即触发失败。
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

| 测试 | 耗时 |
|------|------|
| `TestTaskExecutor` | ~3s（含多线程/异步执行） |

## 重要细节
- 使用 `flaky` 函数模拟需要重试的场景。
- `test_invalid_execution_mode` 确保不支持的模式在初始化时即报错。

## 注意事项
- `TaskExecutor` 是 `TaskStage` 的核心组件，负责具体的函数调用逻辑。
- 相关实现位于 `src/celestialflow/stage/core_executor.py`。
