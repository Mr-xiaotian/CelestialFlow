# 日志持久化测试 (test_log.py)

> 最后更新日期: 2026/06/05

## 作用
验证 `LogInlet` 与 `LogSpout` 能把图启动、任务重试和节点启动等日志事件异步写入日志文件，并保留对应等级文本。

## 覆盖点
- `start_graph()` 写入图启动消息。
- `task_retry()` 写入带异常信息的 WARNING 级别日志。
- `start_stage()` 写入节点启动记录。

## 关键场景
- 在临时目录内启动 `LogSpout`。
- 发送图启动、任务重试和节点启动三类日志事件。
- 轮询检查日志文件存在，并包含 `test message`、`hello world`、`INFO`、`WARNING` 等关键内容。

## 运行方式

```bash
pytest tests/persistence/test_log.py -v
pytest tests/persistence/test_log.py -k "log_persistence" -v
```
