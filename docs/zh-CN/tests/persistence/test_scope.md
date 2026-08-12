# 作用域管理测试 (test_scope.py)

> 📅 最后更新日期: 2026/08/12

## 作用

验证 `celestialflow.persistence.core_scope` 中 `funnel_scope()` 上下文管理器对全局 LogSpout / FallbackSpout 生命周期的自动管理，确保进入作用域时启动后台线程、退出时正确清理并完成持久化。

## 核心测试对象

- `funnel_scope()`: 上下文管理器，自动管理全局 log/fallback spout 的启动与停止。
- `get_log_spout()` / `get_fallback_spout()`: 获取全局单例 spout。
- `get_log_inlet()` / `get_fallback_inlet()`: 获取对应的 inlet 入口。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestFunnelScope` | 4 | 生命周期管理、可复用性、异常安全、单层作用域语义 |

## 关键测试场景

### `test_funnel_scope_starts_and_stops_global_spouts`

验证 `funnel_scope()` 进入时启动两个全局 spout 的后台线程，退出时自动停止并清理线程引用。

- 在作用域内断言 `log_spout._thread` 和 `fallback_spout._thread` 不为空且存活。
- 通过 `get_log_inlet().start_graph()` 写入日志、`get_fallback_inlet().task_in()` + `task_success()` 写 sqlite。
- 退出作用域后断言 `_thread` 为 `None`，且日志文件与 sqlite 文件已持久化并包含正确内容。

### `test_funnel_scope_is_reusable`

验证 `funnel_scope()` 支持多次独立进入与退出。

- 两次进入/退出，每次进入时断言线程重新创建且存活，退出后线程引用为 `None`。

### `test_funnel_scope_wraps_body_error_and_stops_spouts`

验证作用域内部抛出异常时，`funnel_scope()` 仍执行收尾清理。

- 在 `funnel_scope()` 内部抛出 `RuntimeError`。
- 断言异常以 `ExceptionGroup` 形式抛出（匹配 `"Errors occurred during funnel scope"`）。
- 退出后断言两个全局 spout 的 `_thread` 均为 `None`。

### `test_funnel_scope_does_not_claim_nested_reuse`

验证当前 `funnel_scope()` 为单层作用域，不验证嵌套复用语义。

- 进入一次 `funnel_scope()` 执行简单操作后退出，断言 `_thread` 已清理。

## 运行方式

```bash
# 全部执行
pytest tests/persistence/test_scope.py -v

# 按关键字匹配
pytest tests/persistence/test_scope.py -k "lifecycle" -v
pytest tests/persistence/test_scope.py -k "error" -v
pytest tests/persistence/test_scope.py -k "reusable" -v
```

## 注意事项

- 每个用例使用 `autouse` fixture `_cleanup_global_spouts` 前后清理全局 spout，避免后台线程与文件状态串扰。
- 测试使用 `monkeypatch.chdir(tmp_path)` 切换工作目录，确保日志与 sqlite 文件写入临时路径。
- 相关实现位于 `src/celestialflow/persistence/core_scope.py`。
