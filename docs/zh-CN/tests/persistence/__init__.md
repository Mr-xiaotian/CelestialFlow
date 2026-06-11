# persistence 测试包

> 最后更新日期: 2026/06/11

## 作用
`tests/persistence/` 覆盖错误、日志和成功结果三条持久化路径，以及 JSONL 解析工具函数，验证 Inlet / Spout 配对组件在后台线程中能正确落盘或缓存结果。

## 包含的测试文件
- `test_fail.py`: 错误记录写入 JSONL。
- `test_jsonl.py`: JSONL 文件解析与分组工具函数。
- `test_log.py`: 日志记录写入文本文件。
- `test_success.py`: 成功结果缓存为 `(prev_task, result)` 对。

## 运行方式

```bash
pytest tests/persistence -v
pytest tests/persistence -k "fail or jsonl or log or success" -v
```
