# observability 测试包

> 最后更新日期: 2026/06/05

## 作用
`tests/observability/` 覆盖运行状态上报与观测链路，确保 `TaskReporter` 等观测组件能够稳定拉取图状态并对外暴露接口。

## 包含的测试文件
- `test_reporter.py`: 覆盖 reporter 的启动、停止、轮询和异常路径。

## 运行方式

```bash
pytest tests/observability -v
pytest tests/observability/test_reporter.py -v
```
