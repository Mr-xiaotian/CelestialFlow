# runtime 测试包

> 📅 最后更新日期: 2026/06/05

## 作用
`tests/runtime/` 覆盖 CelestialFlow 运行时基础设施，包括任务信封、队列、哈希、计数器、异常类型和剩余时间估算，是调度层与 Stage 层的底层保障。

## 包含的测试文件
- `test_dispatch.py`: 调度循环与分发逻辑。
- `test_envelope.py`: `TaskEnvelope` 属性与哈希行为。
- `test_errors.py`: 自定义异常体系。
- `test_estimators.py`: 耗时与剩余时间估算算法。
- `test_hash.py`: `make_hashable` 与 `object_to_hash`。
- `test_metrics.py`: 计数器与运行指标聚合。
- `test_queue.py`: 任务输入输出队列。
- `test_types.py`: 各类运行时值对象、枚举和上下文包装器。

## 运行方式

```bash
pytest tests/runtime -v
pytest tests/runtime -k "hash or envelope or estimators" -v
```
