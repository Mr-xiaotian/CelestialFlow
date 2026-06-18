# stage 测试包

> 最后更新日期: 2026/06/18

## 作用
`tests/stage/` 覆盖 `TaskStage`、`TaskExecutor` 以及内置 Stage 组件的执行语义，验证任务输入、输出、去重、终止信号、并发模式和生命周期行为。

## 包含的测试文件
- `test_executor.py`: `TaskExecutor` 执行与队列消费。
- `test_stage.py`: `TaskStage` 基础生命周期与配置验证。
- `test_stages.py`: 内置 Stage 组件，如 splitter、router。

## 运行方式

```bash
pytest tests/stage -v
pytest tests/stage -k "executor or stage" -v
```
