# 特定图结构测试 (test_structure.py)

> 📅 最后更新日期: 2026/05/23

## 作用
验证 `TaskLoop` 和 `TaskWheel` 两种预定义含环图结构的专用分析能力，确保它们在非 DAG 场景下的表现符合预期。

## 核心测试对象
- `TaskLoop`: 简单的闭环任务链。
- `TaskWheel`: 中心扩散并带环的轮式结构。

## 关键测试流程
1. **TaskLoop 分析**:
   - 验证 `isDAG` 被正确识别为 `False`。
   - 验证环内所有节点都被分配到同一个逻辑层级。
   - 验证源节点推导能从环中选取一个代表点作为注入点。
2. **TaskWheel 分析**:
   - 验证中心节点（Center）处于第 0 层，而外环节点（Ring）处于第 1 层。
   - 验证 `get_source_stages` 仅返回 Center 节点，确保任务从中心注入。

## 测试重点
- **非 DAG 识别**: 确保含环结构不会被错误地当作 DAG 处理。
- **层级一致性**: 验证在存在循环依赖时，逻辑层级的划分依然符合物理直觉。
- **源节点特化**: 针对特定结构优化的源节点查找逻辑。

## 运行方式

```bash
# 全部执行
pytest tests/graph/test_structure.py -v

# 仅运行 TaskLoop 测试
pytest tests/graph/test_structure.py::TestTaskLoop -v

# 仅运行 TaskWheel 测试
pytest tests/graph/test_structure.py::TestTaskWheel -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskLoop` | ~1s（含图启动与终止） |
| `TestTaskWheel` | ~1s |

## 重要细节
- 使用 `start_graph` 方法启动测试，并配合 `put_termination_signal=True`。
- `TaskWheel` 通过 `set_graph_mode()` 配置后调用 `get_graph_analysis()` 进行分析。
- 测试重点在于"分析结果"（analysis dict）而非"执行结果"。

## 注意事项
- 本测试侧重于 `TaskGraph` 子类的特化行为。
- 相关实现位于 `src/celestialflow/graph/core_structure.py`。
