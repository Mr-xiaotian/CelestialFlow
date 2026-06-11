# 剩余时间估算测试 (test_estimators.py)

> 最后更新日期: 2026/06/11

## 作用
验证 `calc_remaining`、`calc_elapsed` 和 `calc_global_pending` 三个估算函数，确保 CelestialFlow 在节点级和图级都能给出稳定的剩余时间预测。

## 覆盖点
- `calc_remaining`: 基于 `processed / pending / elapsed` 的基础估算。
- `calc_elapsed`: 根据 `StageStatus` 和上轮快照决定是否继续累加耗时。
- `calc_global_pending`: 在 DAG 上把负载从上游传播到下游，覆盖线性链、扇入、扇出、菱形、空图等拓扑。

## 关键场景
- 零值边界：`processed=0`、`pending=0`、空图。
- 状态切换：`NOT_STARTED`、`RUNNING`、`STOPPED` 的累计策略。
- 图结构传播：线性链、扇出、扇入、菱形、瓶颈节点、缺失 map 数据。
- 性质验证：对称性、单调性与"不应出现负值"。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestCalcRemaining` | 7 | 基础比例计算与零值边界 |
| `TestCalcElapsed` | 7 | 基于状态机的时间累计策略 |
| `TestCalcGlobalPending` | 15 | DAG 传播估算：线性链、扇出、扇入、菱形、瓶颈、空图等 |
| `TestPropertyBased` | 3 | 对称性、单调性等属性验证 |

## 运行方式

```bash
pytest tests/runtime/test_estimators.py -v
pytest tests/runtime/test_estimators.py -k "calc_remaining or calc_elapsed" -v
pytest tests/runtime/test_estimators.py -k "global_pending" -v
```
