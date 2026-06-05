# 失败持久化测试 (test_fail.py)

> 最后更新日期: 2026/06/05

## 作用
验证 `FailInlet` 与 `FailSpout` 配合时，任务错误能够被异步写入 JSONL，并同步累加错误总数与内存错误对列表。

## 覆盖点
- `start_graph()` 会记录图结构上下文。
- `task_error()` 会把任务值和异常信息序列化到 `FailSpout`。
- `FailSpout.total_error_num` 与 `get_error_pairs()` 会反映实际处理结果。

## 关键场景
- 在临时目录下启动 spout。
- 连续写入 `ValueError` 与 `RuntimeError` 两类错误。
- 等待后台线程落盘后，断言 JSONL 文件存在，且错误记录数量、类型、任务值都正确。

## 运行方式

```bash
pytest tests/persistence/test_fail.py -v
pytest tests/persistence/test_fail.py -k "fail_persistence" -v
```
