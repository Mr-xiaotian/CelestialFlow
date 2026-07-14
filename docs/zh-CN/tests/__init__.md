# tests 测试包

> 📅 最后更新日期: 2026/06/18

## 作用
`tests/` 目录保存 CelestialFlow 的 pytest 测试集。`tests/__init__.py` 为空文件，本页用于说明测试目录结构。

## 目录结构
- `tests/funnel/`: Inlet / Spout 管道基础行为测试。
- `tests/graph/`: TaskGraph 建图与调度测试。
- `tests/observability/`: 运行状态上报与注入测试。
- `tests/persistence/`: sqlite 容错持久化、日志持久化与 sqlite 工具测试。
- `tests/runtime/`: 信封、队列、哈希、计数器、异常与估算测试。
- `tests/stage/`: TaskStage / TaskExecutor 与内置 Stage 测试。
- `tests/utils/`: 克隆工具与格式化工具测试。
- `tests/conftest.py`: 通用测试 helper。
- `tests/__init__.py`: 空文件，标记测试包。

## 运行方式

```bash
pytest tests -v
pytest tests/runtime -v
pytest tests/stage -k "executor or stage" -v
```
