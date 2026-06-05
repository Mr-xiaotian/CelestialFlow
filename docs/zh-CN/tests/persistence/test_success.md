# 成功结果缓存测试 (test_success.py)

> 最后更新日期: 2026/06/05

## 作用
验证 `SuccessSpout` 会从 `TaskEnvelope` 中提取 `prev` 与 `task`，把成功结果缓存成 `(原任务, 结果)` 对，供后续查询使用。

## 覆盖点
- `TaskEnvelope.prev` 作为原任务标识被正确保留。
- `SuccessSpout` 后台线程会把队列里的 envelope 转换为 success pair。
- `get_success_pairs()` 返回顺序与输入一致。

## 关键场景
- 构造两个带 `prev` 的 `TaskEnvelope`。
- 入队后等待 `SuccessSpout` 消费。
- 断言最终拿到 `('task1', 100)` 和 `('task2', 200)` 两条结果。

## 运行方式

```bash
pytest tests/persistence/test_success.py -v
pytest tests/persistence/test_success.py -k "success_persistence" -v
```
