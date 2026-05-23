# 任务阶段测试 (test_stage.py)

> 最后更新日期: 2026/05/23

## 作用
验证 `celestialflow.stage.core_stage` 中的 `TaskStage` 类，确保节点配置、运行模式切换以及标识管理符合框架设计要求。

## 核心测试对象
- `TaskStage`: 任务图中的基本逻辑单元。

## 关键测试流程
1. **标识管理**: 验证 Stage 的唯一标识（ID）与 `name` 绑定，且在 `set_name` 后能同步更新。
2. **模式校验**:
   - **Stage Mode**: 验证 `serial` (顺序隔离) 和 `thread` (线程隔离) 模式的配置合法性。
   - **Execution Mode**: 验证 `serial`, `thread`, `async` 三种执行模式的配置合法性。
   - **非法值**: 验证配置错误模式时抛出 `StageModeError` 或 `ExecutionModeError`。
3. **摘要信息**: 验证 `get_summary()` 返回的信息包含关键的模式标记（如 `thread-20` 表示线程池大小为 20）。
4. **Lambda 支持**: 验证在 `thread` 隔离模式下，匿名函数可以被正确序列化/调用（由内部 Executor 配合）。

## 测试重点
- **配置严谨性**: 确保在初始化阶段就能拦截错误的模式组合。
- **元数据同步**: 验证 Stage 名称作为图引用键的稳定性。
- **模式语义**: 区分“节点隔离模式 (Stage Mode)”与“任务执行模式 (Execution Mode)”的不同职责。

## 运行方式

```bash
# 全部执行
pytest tests/stage/test_stage.py -v

# 仅运行标识管理测试
pytest tests/stage/test_stage.py -k "name" -v

# 仅运行模式校验测试
pytest tests/stage/test_stage.py -k "mode" -v

# 仅运行 Lambda 支持测试
pytest tests/stage/test_stage.py -k "lambda" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskStage` | ~0.2s（纯配置验证，无任务执行） |

## 重要细节
- `TaskStage` 不直接执行任务，而是通过配置 `TaskExecutor` 和管理 `Queue` 来组织运行。
- `test_lambda_allowed_in_thread` 是对线程隔离模式下任务函数灵活性的重要验证。

## 注意事项
- 任务阶段是构成 TaskGraph 的基础。
- 相关实现位于 `src/celestialflow/stage/core_stage.py`。
