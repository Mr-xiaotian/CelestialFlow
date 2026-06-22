# observability 测试包

> 📅 最后更新日期: 2026/06/22

## 作用
`tests/observability/` 覆盖运行状态观测与任务注入/上报机制，确保 `BaseObserver` 生命周期回调以及 `TaskReporter` 任务注入与错误推送行为符合预期。

## 包含的测试文件
- `test_observer.py`: 覆盖 Observer 生命周期回调、多观察器支持、动态管理。
- `test_reporter_injection.py`: 覆盖 `TaskReporter._pull_and_inject_tasks()` 的节点映射注入与日志记录逻辑。

## 运行方式

```bash
pytest tests/observability -v
pytest tests/observability/test_observer.py -v
pytest tests/observability/test_reporter_injection.py -v
```
