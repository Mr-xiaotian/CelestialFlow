# persistence 测试包

> 📅 最后更新日期: 2026/06/22

## 作用
`tests/persistence/` 覆盖错误容错、日志记录和 sqlite 工具函数三条持久化路径，验证 Inlet / Spout 配对组件在后台线程中能正确落盘或批量刷新日志。

## 包含的测试文件
- `test_fallback.py`: 错误与成功结果的 sqlite 持久化（`FallbackInlet` / `FallbackSpout`）。
- `test_log.py`: 日志记录批量写入文本文件（`LogInlet` / `LogSpout`）。
- `test_splite.py`: sqlite 工具函数（建表、增删改查、状态迁移、分组读取）。

## 运行方式

```bash
pytest tests/persistence -v
pytest tests/persistence -k "fallback or log or splite" -v
```
