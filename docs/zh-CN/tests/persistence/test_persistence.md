# 持久化集成测试 (test_persistence.py)

> 最后更新日期: 2026/05/23

## 作用
验证持久化子系统的端到端集成逻辑，确保任务的成功结果、失败错误以及系统日志能通过 Inlet/Spout 链路正确写入目标介质。

## 核心测试对象
- `FailInlet / FailSpout`: 错误任务的异步持久化链路。
- `LogInlet / LogSpout`: 系统日志的异步持久化链路。
- `SuccessSpout`: 成功任务的内存缓存管理。

## 关键测试流程
1. **错误持久化**:
   - 通过 `FailInlet` 注入任务错误。
   - 验证 `FailSpout` 后台线程能正确创建 JSONL 文件并写入记录。
   - 验证 `get_error_pairs()` 能重新读取并还原错误记录。
2. **日志持久化**:
   - 验证不同级别（INFO, WARNING）的日志能被正确记录到文件。
   - 验证文件内容包含时间戳（隐含）、级别和消息正文。
3. **成功任务记录**:
   - 验证 `SuccessSpout` 能在内存中缓存 `(输入任务, 输出结果)` 配对，以便后续审计。

## 测试重点
- **异步写入**: 验证 Spout 的后台线程模式能正常启动、处理队列并停止。
- **文件路径控制**: 使用 `monkeypatch` 控制当前工作目录，确保测试产物不污染主目录。
- **数据完整性**: 验证从 `TaskEnvelope` 到最终持久化记录的字段转换准确性。

## 运行方式

```bash
# 全部执行
pytest tests/persistence/test_persistence.py -v

# 仅运行错误持久化测试
pytest tests/persistence/test_persistence.py -k "fail" -v

# 仅运行日志持久化测试
pytest tests/persistence/test_persistence.py -k "log" -v

# 仅运行成功任务记录测试
pytest tests/persistence/test_persistence.py -k "success" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestPersistenceIntegration` | ~2s（含后台线程 I/O 等待） |

## 重要细节
- 集成测试使用了 `time.sleep(0.2)` 等待后台线程完成 IO 操作。
- `test_fail_persistence` 验证了 `error_source` 标记的正确传递。

## 注意事项
- 错误和日志持久化目前主要基于本地文件，而成功持久化暂为内存实现。
- 相关代码位于 `tests/persistence/`。
