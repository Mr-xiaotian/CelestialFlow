# Web 服务 API 测试 (test_server.py)

> 📅 最后更新日期: 2026/06/28

## 作用

验证 `celestialflow.web.core_server` 提供的 RESTful API，确保 Web 仪表盘能够正确展示图状态、拉取配置、注入任务并浏览错误日志，同时验证快照数据的隔离性。

## 核心测试对象

- `TaskWebServer`: 基于 FastAPI 实现的监控与交互服务器。

## 关键测试场景

### 快照隔离
- `test_store_snapshot_methods_return_isolated_copies`: 验证 server 各快照接口返回深拷贝，修改返回值不影响内部 store。

### 静态资源渲染
- `test_index_page`: 验证首页 `/` 能正确返回包含 `dashboard` 容器的 HTML 页面。

### 配置拉取
- `test_config_api`: 验证前端所需的运行时参数（刷新频率、主题等）能被正确获取。

### 服务端状态
- `test_server_state_api`: 验证 reporter 拉取的服务端同步状态，包括轮询间隔、当前图标识、结构/分析状态、失败事件水位线。

### 状态同步 (Rev 机制)
- `test_status_push_pull`:
  - 验证 `push_status` 能成功保存快照。
  - 验证 `pull_status` 支持增量更新：当 `known_rev` 与服务器当前版本一致时，返回空数据以节省带宽。

### 任务注入
- `test_task_injection`: 验证通过 POST 接口注入的任务能被正确暂存，并由调度器通过 GET 接口消费，消费后被清空。
- `test_task_injection_overwrites_tasklist_per_node`: 验证新的 push 会逐个节点更新 task list，而非追加。
- `test_task_injection_requires_tasklist_mapping`: 验证非法 payload（非列表值）返回 422。
- `test_termination_injection_requires_string_array`: 验证终止符注入接口要求请求体为字符串数组，否则返回 422。

### 错误管理
- `test_errors_pagination`:
  - 验证错误记录的批量推送。
  - 验证分页逻辑：检查 `total_pages`、`total` 和当前页数据量。
  - 验证按节点（`node`）过滤逻辑。
  - 验证关键词（`keyword`）过滤逻辑。
  - 验证排序（`sort_order`）：支持 `newest` 和 `oldest` 两种。
- `test_push_errors_appends_for_same_graph`: 相同 `graph_id` 下多次推送错误仅追加，不覆盖。
- `test_push_errors_duplicate_append_is_idempotent`: 重复推送相同 `event_id` 不会产生重复行。
- `test_newer_graph_replaces_previous_graph_context`: 新 `graph_id` 到来时清空旧错误缓存。
- `test_stale_graph_pushes_are_ignored`: 切换到新图后，旧图的迟到推送不应污染当前缓存。
- `test_push_errors_meta_route_removed`: `/api/push_errors_meta` 已删除，访问返回 404。

## 测试覆盖矩阵

| 测试函数 | 覆盖目标 |
|----------|----------|
| `test_store_snapshot_methods_return_isolated_copies` | 快照返回深拷贝 |
| `test_index_page` | 首页 HTML 渲染 |
| `test_config_api` | `/api/pull_config` 配置拉取 |
| `test_server_state_api` | `/api/pull_server_state` 服务端状态 |
| `test_push_errors_meta_route_removed` | 旧端点已删除 |
| `test_status_push_pull` | 状态推送与增量拉取 |
| `test_task_injection` | 任务与终止符注入、消费、清空 |
| `test_task_injection_overwrites_tasklist_per_node` | 按节点覆盖 task list |
| `test_task_injection_requires_tasklist_mapping` | 任务注入参数校验 |
| `test_termination_injection_requires_string_array` | 终止符注入参数校验 |
| `test_errors_pagination` | 错误分页、过滤、排序 |
| `test_push_errors_appends_for_same_graph` | 同图错误追加 |
| `test_push_errors_duplicate_append_is_idempotent` | 重复推送幂等 |
| `test_newer_graph_replaces_previous_graph_context` | 新图上下文切换 |
| `test_stale_graph_pushes_are_ignored` | 过期推送忽略 |

## 测试重点

- **Rev 版本控制**: 确保前端刷新逻辑的高效性，避免冗余数据传输。
- **分页准确性**: 验证后端在处理错误记录时的偏移量计算。
- **任务一致性**: 确保注入的任务在拉取消费后被正确清除，防止重复处理。
- **快照隔离**: 确保前端获取的数据不会因为内部状态突变而产生不一致。
- **参数校验**: 验证注入接口对非法 payload 返回 422，避免下游处理错误数据。

## 运行方式

```bash
# 全部执行
pytest tests/web/test_server.py -v

# 仅运行状态同步测试
pytest tests/web/test_server.py -k "status" -v

# 仅运行任务注入测试
pytest tests/web/test_server.py -k "injection" -v

# 仅运行错误管理测试
pytest tests/web/test_server.py -k "errors" -v

# 仅运行配置拉取测试
pytest tests/web/test_server.py -k "config" -v
```

## 重要细节

- 使用 `FastAPI TestClient` 进行模拟请求，不会真实启动端口监听。
- 快照隔离测试直接操作 `web_server` fixture（由 `conftest.py` 提供），其他测试使用 `client` fixture。
- 测试在每个函数运行前创建新的 server 实例。

## 注意事项

- Web 服务是 CelestialFlow 的可视化窗口。
- 相关实现位于 `src/celestialflow/web/core_server.py`。
