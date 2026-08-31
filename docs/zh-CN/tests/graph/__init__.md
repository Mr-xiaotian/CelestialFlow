# graph 测试包

> 📅 最后更新日期: 2026/08/31

## 作用
`tests/graph/` 覆盖任务图构建、拓扑分析、结构渲染与图级调度行为，以及 `TaskLoop`、`TaskWheel` 等含环图结构的专用测试，主要对应 `celestialflow.graph` 模块。

## 包含的测试文件
- `test_estimators.py`: 剩余时间估算与 DAG 负载传播算法。
- `test_graph.py`: 覆盖 `TaskGraph` 的建图、调度、错误收集和生命周期。
- `test_order_graph.py`: 覆盖 `OrderGraph` 构建、源节点识别、层级计算、SCC 划分与深图回归等图分析基础能力。
- `test_render.py`: 覆盖结构图渲染为带边框的树形文本列表（替代旧的序列化测试）。
- `test_structure.py`: 覆盖 `TaskLoop` 和 `TaskWheel` 含环图结构的专用分析及输入校验。

## 运行方式

```bash
pytest tests/graph -v
pytest tests/graph -k "graph or order_graph or structure or render" -v
```
