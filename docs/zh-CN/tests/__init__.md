# tests 测试包

> 最后更新日期: 2026/06/05

## 作用
`tests/` 目录保存 CelestialFlow 的 pytest 测试集。`tests/__init__.py` 为空文件，本页用于说明测试目录结构。

## 目录结构
- `tests/funnel/`: Inlet / Spout 管道基础行为测试。
- `tests/graph/`: TaskGraph 建图与调度测试。
- `tests/observability/`: 运行状态上报测试。
- `tests/persistence/`: 错误、日志、成功结果持久化测试。
- `tests/runtime/`: 信封、队列、哈希、计数器、异常与估算测试。
- `tests/stage/`: TaskStage / TaskExecutor 与内置 Stage 测试。
- `tests/web/`: Web API 与服务集成测试。
- `tests/conftest.py`: 通用测试 helper。

## 运行方式

```bash
pytest tests -v
pytest tests/runtime -v
pytest tests/stage -k "executor or stage" -v
```
