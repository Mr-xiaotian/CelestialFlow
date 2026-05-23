# 任务图核心功能测试 (test_graph.py)

> 最后更新日期: 2026/05/23

## 作用
全面验证 `TaskGraph` 及其各种拓扑子类（`TaskChain`, `TaskCross`, `TaskGrid`）的核心功能，涵盖同步/异步执行、错误传播、拓扑分析及统计汇总。

## 核心测试对象
- `TaskGraph`: 通用任务图容器。
- `TaskChain`, `TaskCross`, `TaskGrid`: 预定义拓扑结构。
- `StageRuntime`: 运行时状态管理。

## 关键测试流程
1. **基础拓扑执行**: 验证线性 DAG、扇入、扇出场景下任务结果的正确传递。
2. **异步与并发**: 
   - 验证 `execution_mode="async"` 下的任务流。
   - 覆盖 `stage_mode` (serial/thread) 与 `execution_mode` (serial/thread/async) 的 2x3 矩阵组合。
3. **错误鲁棒性**: 验证上游任务失败时，错误不会阻塞图运行，且下游仅接收成功结果。
4. **拓扑分析**: 自动推导 `isDAG` 状态、计算层级字典及识别源节点。
5. **复杂结构**: 验证网格（Grid）、全连接（Cross）等复杂连接模式的任务分发逻辑。
6. **循环图处理**: 验证含环图的 `isDAG=False` 检测及层级分配。

## 测试重点
- **执行模式组合**: 确保线程隔离与异步执行在各种组合下表现稳定。
- **自动源推导**: 确保无论图多复杂，都能准确找到注入任务的入口点。
- **摘要统计**: 验证 `get_graph_summary` 返回的任务计数（成功/失败/剩余）准确无误。

## 重要细节
- **终止信号**: 含环图测试使用 `put_termination_signal=True` 确保测试能够退出。
- **统计快照**: 单元测试中需手动调用 `collect_runtime_snapshot()` 以生成统计汇总。
- **Lambda 支持**: 验证 `TaskStage` 可以直接接受 lambda 函数。

## 注意事项
- 测试涉及多线程同步，部分用例执行时间较长。
- 异步测试使用 `async_add_one` 等辅助协程。
