# graph 测试包

> 最后更新日期: 2026/06/18

## 作用
`tests/graph/` 覆盖任务图构建、拓扑分析、结构导出与图级调度行为，以及 `TaskLoop`、`TaskWheel` 等含环图结构的专用测试，主要对应 `celestialflow.graph` 模块。

## 包含的测试文件
- `test_analysis.py`: 覆盖 `OrderGraph` 构建、源节点识别与层级计算等图分析基础能力。
- `test_graph.py`: 覆盖 `TaskGraph` 的建图、调度、错误收集和生命周期。
- `test_serialize.py`: 覆盖结构图 JSON / 文本导出逻辑。
- `test_structure.py`: 覆盖 `TaskLoop` 和 `TaskWheel` 含环图结构的专用分析。

## 运行方式

```bash
pytest tests/graph -v
pytest tests/graph -k "graph or analysis or structure" -v
```
