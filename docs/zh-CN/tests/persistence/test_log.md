# 日志持久化测试 (test_log.py)

> 最后更新日期: 2026/06/18

## 作用
验证 `celestialflow.persistence.core_log` 中的 `LogInlet` 与 `LogSpout`，确保图生命周期事件（启动/结束）、任务重试事件和节点启动事件能异步批量刷新到日志文件，并保留正确的日志等级标记。

## 核心测试对象

| 类 | 说明 |
|----|------|
| `LogInlet` | 以 `log_level='INFO'` 初始化，提供 `start_graph()` / `task_retry()` / `end_graph()` / `start_stage()` 等写入方法 |
| `LogSpout` | 后台线程将队列中的记录批量刷新到日志文件 |

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestLogPersistence` | 1 | 完整日志生命周期：start_graph → task_retry → end_graph → start_stage，验证日志文件包含全部内容与等级标记 |

## 关键测试场景

### `test_log_persistence`

- `start_graph("test_graph", ['test message'])` 写入图启动消息
- `task_retry('func', 'hello world', 1, ValueError('oops'), 0, 1)` 写入带异常信息的 WARNING 级别日志
- `end_graph("test_graph", 1.0)` 写入图结束事件
- `start_stage('stage', 'normal', 'parallel-4')` 写入节点启动记录
- 通过 `wait_until` 轮询等待日志文件存在且包含 'test message' 和 'hello world' 等关键内容
- 最终断言日志文件中同时存在 `INFO` 和 `WARNING` 等级标记

## 运行方式

```bash
pytest tests/persistence/test_log.py -v
pytest tests/persistence/test_log.py -k "log_persistence" -v
```

## 注意事项

- 测试使用 `monkeypatch.chdir(tmp_path)` 切换工作目录，确保日志文件写入临时路径
- 日志文件的具体路径通过 `spout.log_path` 属性获取
- 相关实现位于 `src/celestialflow/persistence/core_log.py`
