# tests/persist/test_log.py

> 📅 最后更新日期: 2026/10/09

## 作用

验证 `celestialflow.persist.core_log` 中的 `LogInlet` 与 `LogSpout`，确保图生命周期事件（启动 / 结束）、节点启动事件、任务重试事件与跳过事件能异步批量刷新到日志文件，并保留正确的日志等级标记。

## 核心测试对象

| 类 / 对象 | 来源 | 说明 |
|-----------|------|------|
| `LogInlet` | `celestialflow.persist.core_log` | 以 `MetricsObserver` 与 `log_level` 初始化，提供 `on_graph_start` / `on_task_retry` / `on_graph_end` / `on_node_start` / `on_task_skip` 等事件写入方法 |
| `LogSpout` | `celestialflow.persist.core_log` | 后台线程将队列中的记录批量刷新到日志文件，路径通过 `spout.log_path` 获取 |
| `MetricsObserver` | `celestialflow.observer` | 供 LogInlet 查询节点指标以生成日志内容 |
| 事件类型 | `celestialflow.observer` | `GraphStartEvent` / `TaskRetryEvent` / `GraphEndEvent` / `NodeStartEvent` / `TaskSkipEvent` |

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestLogPersistence` | 2 | 完整日志生命周期、跳过日志 |

## 关键测试场景

### `test_log_persistence`

- 构造 `LogInlet(MetricsObserver(), log_level='INFO').bind_spout(spout)`，`spout.start()` 启动后台线程。
- 依次触发 `on_graph_start`（图名 / 模式 / 结构列表 / 节点元信息）、`on_task_retry`（携带异常 → WARNING 级）、`on_graph_end`、`on_node_start`。
- 通过 `wait_until` 轮询等待日志文件存在且包含 `| node |` 与 `hello world` 等关键内容。
- 最终断言日志文件中同时存在 `INFO` 与 `WARNING` 等级标记。

### `test_skip_log`

- 构造 `LogInlet(MetricsObserver(), log_level='SUCCESS').bind_spout(spout)`。
- 触发 `on_task_skip`（携带 `[7->8*]` 事件 ID 区间标记）。
- 断言日志文件包含 `hello world`、`skipped`、`[7->8*]` 与 `SUCCESS` 等级标记。

## 运行方式

```bash
pytest tests/persist/test_log.py -v
pytest tests/persist/test_log.py -k "log_persistence" -v
pytest tests/persist/test_log.py -k "skip" -v
```

## 注意事项

- 测试使用 `monkeypatch.chdir(tmp_path)` 切换工作目录，确保日志文件写入临时路径下的 `logs/` 目录。
- 日志文件的具体路径通过 `spout.log_path` 属性获取。
- `LogInlet` 通过 `bind_spout` 绑定到 `LogSpout`，事件经队列异步写入文件。
- 相关实现位于 `src/celestialflow/persist/core_log.py`。