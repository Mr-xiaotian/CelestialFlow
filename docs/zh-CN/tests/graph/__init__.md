# graph 测试包

> 最后更新日期: 2026/06/05

## 作用
`tests/graph/` 覆盖任务图构建、拓扑分析、结构导出与图级调度行为，主要对应 `celestialflow.graph` 模块。

## 包含的测试文件
- `test_analysis.py`: 覆盖源节点识别、层级计算和 networkx 图分析辅助函数。
- `test_graph.py`: 覆盖 `TaskGraph` 的建图、调度、错误收集和生命周期。
- `test_serialize.py`: 覆盖结构图 JSON / 文本导出逻辑。

## 运行方式

```bash
pytest tests/graph -v
pytest tests/graph -k "graph or analysis" -v
```
