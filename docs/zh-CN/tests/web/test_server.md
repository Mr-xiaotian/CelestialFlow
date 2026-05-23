# Web 服务 API 测试 (test_server.py)

> 最后更新日期: 2026/05/23

## 作用
验证 `celestialflow.web.core_server` 提供的 RESTful API，确保 Web 仪表盘能够正确展示图状态、拉取配置、注入任务并浏览错误日志。

## 核心测试对象
- `TaskWebServer`: 基于 FastAPI 实现的监控与交互服务器。

## 关键测试流程
1. **静态资源渲染**: 验证首页 `/` 能正确返回包含 `dashboard` 容器的 HTML 页面。
2. **状态同步 (Rev 机制)**:
   - 验证 `push_status` 能成功保存快照。
   - 验证 `pull_status` 支持增量更新：当 `known_rev` 与服务器当前版本一致时，返回空数据以节省带宽。
3. **任务注入**: 验证通过 POST 接口注入的任务能被正确暂存，并由调度器通过 GET 接口消费。
4. **错误管理**:
   - 验证错误记录的批量推送。
   - 验证分页逻辑：检查 `total_pages` 和当前页数据量。
   - 验证过滤逻辑：确保能按 Stage 节点名称筛选错误。
5. **配置拉取**: 验证前端所需的运行时参数（如刷新频率、主题）能被正确获取。

## 测试重点
- **Rev 版本控制**: 确保前端刷新逻辑的高效性，避免冗余数据传输。
- **分页准确性**: 验证后端在处理大量错误记录时的偏移量计算。
- **任务一致性**: 确保注入的任务在拉取消费后被正确清除，防止重复处理。

## 运行方式

```bash
# 全部执行
pytest tests/web/test_server.py -v

# 仅运行状态同步测试
pytest tests/web/test_server.py -k "status" -v
pytest tests/web/test_server.py -k "rev" -v

# 仅运行任务注入测试
pytest tests/web/test_server.py -k "inject" -v

# 仅运行错误管理测试
pytest tests/web/test_server.py -k "error" -v

# 仅运行配置拉取测试
pytest tests/web/test_server.py -k "config" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskWebServer` | ~0.5s（模拟 HTTP 请求） |

## 重要细节
- 使用 `FastAPI TestClient` 进行模拟请求。
- 注入任务测试中使用了 `datetime.now().isoformat()` 模拟真实时间戳。

## 注意事项
- Web 服务是 CelestialFlow 的可视化窗口。
- 相关实现位于 `src/celestialflow/web/core_server.py`。
