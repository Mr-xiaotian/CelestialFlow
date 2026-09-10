# 节点基类测试 (test_node.py)

> 📅 最后更新日期: 2026/09/10

## 作用

验证 `celestialflow.node.core_node.BaseTaskNode`（通过公共子类 `TaskExecutor` 间接覆盖）提供的通用配置、绑定与启动异常聚合行为。

## 核心测试对象

| 类 / 函数 | 角色 | 说明 |
|-----------|------|------|
| `add_one(x)` | 测试回调 | 同步加一函数 |
| `async_add_one(x)` | 测试回调 | 异步加一协程函数 |
| `TestBaseTaskNodeConfig` | 用例类 | 覆盖名称、执行模式、快照、切换模式时前驱绑定不丢失 |
| `TestBaseTaskNodeStartErrors` | 用例类 | 覆盖 `start` / `start_async` 异常聚合行为 |

## 关键测试场景

### `TestBaseTaskNodeConfig` — 配置与绑定

| 用例 | 覆盖目标 |
|------|---------|
| `test_node_name_identity` | 节点名称直接来自构造参数 `name` |
| `test_node_name_changes_with_name` | 通过 `set_name(...)` 修改名称后 `get_name()` 同步更新 |
| `test_valid_execution_mode_serial` | 支持 `execution_mode="serial"` |
| `test_valid_execution_mode_thread` | 支持 `execution_mode="thread"` |
| `test_valid_execution_mode_async` | 支持 `execution_mode="async"`（使用 `async_add_one`） |
| `test_invalid_execution_mode` | 非法模式应抛 `InvalidOptionError` |
| `test_snapshot_contains_execution_mode` | `snapshot(interval=0.1)` 返回的字典包含 `execution_mode` 字段 |
| `test_prev_binding_survives_execution_mode_switch` | 通过 `prev_binding` 绑定前驱后，调用 `set_execution_mode("thread")` 不会破坏已建立的计数关系（`metrics.get_task_count()` 在前后一致） |

### `TestBaseTaskNodeStartErrors` — 启动异常聚合

| 用例 | 覆盖目标 |
|------|---------|
| `test_start_raises_exception_group_after_finish` | 通过 `monkeypatch` 让 `_prepare_start` 抛 `ValueError("prepare failed")`、`_finish_start` 返回 `[RuntimeError("finish failed")]`；同步 `start()` 最终抛 `ExceptionGroup`，其中两条异常按"prepare → finish"顺序 |
| `test_start_async_raises_exception_group_after_finish` | 异步版本同样把 prepare 异常与 finish 异常聚合成 `ExceptionGroup` 抛出 |

## 关键数据流

```mermaid
flowchart TB
    Start[start]
    Prep[_prepare_start]
    Mode{execution_mode}
    Serial[dispatch_serial]
    Thread[dispatch_thread]
    Async[dispatch_async]
    Finish[_finish_start]
    Agg[ExceptionGroup 聚合抛出]

    Start --> Prep
    Prep --> Mode
    Mode -- serial --> Serial
    Mode -- thread --> Thread
    Mode -- async --> Async
    Serial --> Finish
    Thread --> Finish
    Async --> Finish
    Finish --> Agg
```

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestBaseTaskNodeConfig` | 8 | 名称标识与修改、三种合法执行模式、非法模式报错、快照字段、切换模式不破坏前驱绑定 |
| `TestBaseTaskNodeStartErrors` | 2 | 同步 / 异步 `start*` 异常聚合 |
| **合计** | **10** | |

## 运行方式

```bash
# 全部执行
pytest tests/node/test_node.py -v

# 仅运行配置相关用例
pytest tests/node/test_node.py -k "Config" -v

# 仅运行启动异常聚合用例
pytest tests/node/test_node.py -k "StartErrors" -v

# 仅运行执行模式相关用例
pytest tests/node/test_node.py -k "execution_mode" -v
```

## 性能参考

| 测试类 | 耗时 |
|--------|------|
| `TestBaseTaskNodeConfig` | < 0.5s |
| `TestBaseTaskNodeStartErrors` | < 0.5s |

## 注意事项

- `test_prev_binding_survives_execution_mode_switch` 是回归测试，覆盖之前"`TaskMetrics` 在切换执行模式时重建计数器导致前驱绑定失效"的问题；现版本固定 `TaskMetrics` 使用同一把 `threading.Lock` 以保证统计对象稳定。
- `TestBaseTaskNodeStartErrors` 通过 `monkeypatch.setattr` 替换 `_prepare_start` 与 `_finish_start` 两个**内部钩子**；这要求测试与实现位于同一包内（已通过 `celestialflow.node` 公开导出保证）。
- `ExceptionGroup` 仅在 Python 3.11+ 可用，本仓库基于 Python 3.14 满足要求。
- 相关实现位于 `src/celestialflow/node/core_node.py`。
