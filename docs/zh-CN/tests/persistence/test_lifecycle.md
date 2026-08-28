# 生命周期持久化测试 (test_lifecycle.py)

> 📅 最后更新日期: 2026/08/26

## 作用

验证 `celestialflow.persistence.core_lifecycle` 中的 `LifecycleInlet` 与 `LifecycleSpout` 配对组件，确保任务生命周期事件（进入、成功、失败、重复）通过后台线程写入 sqlite 文件，并可按 stage 维度读取 task-error 对和 task-result 对。

## 核心测试对象

- `LifecycleInlet`: 通过 `task_in()` / `task_success()` / `task_fail()` / `task_duplicate()` 将生命周期事件经 `_funnel()` 入队。
- `LifecycleSpout`: 后台线程消费队列中的事件并落盘到 sqlite 文件，支持 `get_task_error_pairs()` / `get_task_result_pairs()` 查询。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestLifecyclePersistence` | 2 | 完整生命周期持久化、成功结果持久化 |

## 关键测试场景

### `test_lifecycle_persistence`

覆盖 `task_in` → `task_fail`、`task_in` → `task_success`、`task_in` → `task_duplicate` 三条生命周期链路（s1 / s2 / s3 三个 stage）。

- `task_fail(event_id=1, error_id=21, error=ValueError("oops"))` 将 s1 的 pending 记录晋升为 failed，最终记录以 `error_id`（21）作为落库 `event_id`，并绑定错误类型与错误消息。
- `task_success(event_id=2, result="ok2")` 将 s2 的 pending 记录晋升为 success，保留原 `event_id`（2）并写入结果。
- `task_duplicate(event_id=3)` 删除 s3 的 pending 记录，最终数据库中不残留该记录。
- 断言 sqlite 文件创建成功（`.sqlite3` 后缀），`get_task_error_pairs("s1")` 返回 `[("data1", ("ValueError", "oops"))]`。
- 直接查询 records 表并按 `id` 排序，验证 `event_id` 序列为 `[21, 2]`，逐字段核对 `stage` / `status` / `error_type` / `error_message` / `task_json` / `result_json`，且两条记录的 `ts` 均大于 0。

### `test_success_persistence`

覆盖成功结果的持久化与回读。

- 对 s1、s2 分别执行 `task_in` + `task_success`（结果 100 / 200）。
- 断言 `get_task_result_pairs("s1")` 返回 `[("task1", 100)]`，即 task-result 对按 stage 准确读回。

```mermaid
flowchart LR
    subgraph Inlet
        A[task_in] --> B[task_success]
        A --> C[task_fail]
        A --> D[task_duplicate]
    end
    subgraph Spout
        E[消费队列] --> F[写入 sqlite]
    end
    A -.->|queue| E
    B -.->|queue| E
    C -.->|queue| E
    D -.->|queue| E
    F --> G[get_task_error_pairs]
    F --> H[get_task_result_pairs]
```

## 运行方式

```bash
# 全部执行
pytest tests/persistence/test_lifecycle.py -v

# 按关键字匹配
pytest tests/persistence/test_lifecycle.py -k "lifecycle" -v
pytest tests/persistence/test_lifecycle.py -k "success" -v
```

## 注意事项

- 测试通过 `monkeypatch.chdir(tmp_path)` 将工作目录切换到临时目录，sqlite 文件（`./lifecycles/<日期>/flow_lifecycle(<时间>).sqlite3`）在测试结束后自动清理。
- 失败记录的 `event_id` 会被替换为 `task_fail()` 传入的 `error_id`，与该 stage 后续的错误查询/推送语义保持一致。
- 相关实现在 `src/celestialflow/persistence/core_lifecycle.py`。
