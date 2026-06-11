# 任务阶段测试 (test_stage.py)

> 最后更新日期: 2026/06/11

## 作用
验证 `celestialflow.stage.core_stage` 中的 `TaskStage` 类，确保节点配置、运行模式切换以及标识管理符合框架设计要求。

## 核心测试对象
- `TaskStage`: 任务图中的基本逻辑单元。

## 测试覆盖矩阵

| 用例 | 覆盖目标 |
|------|----------|
| `test_stage_name_identity` | name 即为唯一标识 |
| `test_stage_name_changes_with_name` | `set_name()` 后标识同步更新 |
| `test_valid_stage_mode_serial` | `stage_mode="serial"` 合法 |
| `test_valid_stage_mode_thread` | `stage_mode="thread"` 合法 |
| `test_invalid_stage_mode` | 非法 `stage_mode` 抛出 `StageModeError` |
| `test_valid_execution_mode_serial` | `execution_mode="serial"` 合法 |
| `test_valid_execution_mode_thread` | `execution_mode="thread"` 合法 |
| `test_valid_execution_mode_async` | `execution_mode="async"` 合法 |
| `test_invalid_execution_mode` | 非法 `execution_mode` 抛出 `ExecutionModeError` |
| `test_summary_contains_stage_mode` | `get_summary()` 包含 `stage_mode` 和 `execution_mode` |
| `test_lambda_allowed_in_thread` | thread 模式下允许 lambda 函数 |

## 测试重点
- **配置严谨性**: 确保在初始化阶段就能拦截错误的模式组合。
- **元数据同步**: 验证 Stage 名称作为图引用键的稳定性。
- **模式语义**: 区分"节点隔离模式 (Stage Mode)"与"任务执行模式 (Execution Mode)"的不同职责。

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
| `TestTaskStageConfig` | ~0.2s（纯配置验证，无任务执行） |

## 重要细节
- `TaskStage` 不直接执行任务，而是通过配置 `TaskExecutor` 和管理 `Queue` 来组织运行。
- `test_lambda_allowed_in_thread` 是对线程隔离模式下任务函数灵活性的重要验证。

## 注意事项
- 任务阶段是构成 TaskGraph 的基础。
- 相关实现位于 `src/celestialflow/stage/core_stage.py`。
