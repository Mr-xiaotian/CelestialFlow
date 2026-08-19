# 任务阶段测试 (test_stage.py)

> 📅 最后更新日期: 2026/08/19

## 作用
验证 `celestialflow.stage.core_stage` 中的 `TaskStage` 类，确保节点配置、运行模式切换以及标识管理符合框架设计要求。

## 核心测试对象
- `TaskStage`: 任务图中的基本逻辑单元。

## 测试覆盖矩阵

### `TestTaskStageConfig` — 节点配置验证（8 个用例）

| 用例 | 覆盖目标 |
|------|----------|
| `test_stage_name_identity` | name 即为唯一标识 |
| `test_stage_name_changes_with_name` | `set_name()` 后标识同步更新 |
| `test_valid_execution_mode_serial` | `execution_mode="serial"` 合法 |
| `test_valid_execution_mode_thread` | `execution_mode="thread"` 合法 |
| `test_valid_execution_mode_async` | `execution_mode="async"` 合法 |
| `test_invalid_execution_mode` | 非法 `execution_mode` 抛出 `InvalidOptionError` |
| `test_summary_contains_execution_mode` | `get_summary()` 包含 `execution_mode` 字段 |
| `test_prev_binding_survives_execution_mode_switch` | 前驱绑定在 execution_mode 切换后指标仍保持同步 |

### `TestTaskStageStartErrors` — 异常组收集（2 个用例）

| 用例 | 覆盖目标 |
|------|----------|
| `test_start_raises_exception_group_after_finish` | 同步 start 在 finish 后统一抛出收集到的异常 |
| `test_start_async_raises_exception_group_after_finish` | 异步 start_async 在 finish 后统一抛出异常 |

## 测试重点
- **配置严谨性**: 确保在初始化阶段就能拦截错误的执行模式，非法模式抛出 `InvalidOptionError`。
- **元数据同步**: 验证 Stage 名称作为图引用键的稳定性，以及前驱绑定在 execution_mode 切换后仍保持同步。
- **异常组收集**: 同步/异步 start 生命周期中的前置与后置异常应统一以 `ExceptionGroup` 形式抛出。

## 运行方式

```bash
# 全部执行
pytest tests/stage/test_stage.py -v

# 仅运行标识管理测试
pytest tests/stage/test_stage.py -k "name" -v

# 仅运行执行模式校验测试
pytest tests/stage/test_stage.py -k "mode" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskStageConfig` | ~0.2s（纯配置验证，无任务执行） |
| `TestTaskStageStartErrors` | ~0.3s（含 monkeypatch 异常注入） |

## 重要细节
- `TaskStage` 不直接执行任务，而是通过配置 `TaskExecutor` 和管理 `Queue` 来组织运行。
- `TestTaskStageStartErrors` 通过 monkeypatch 注入 `_prepare_start` 和 `_finish_start` 的异常来验证异常组收集机制。

## 注意事项
- 任务阶段是构成 TaskGraph 的基础。
- 相关实现位于 `src/celestialflow/stage/core_stage.py`。
