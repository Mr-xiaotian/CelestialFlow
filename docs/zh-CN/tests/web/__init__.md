# web 测试包

> 最后更新日期: 2026/06/11

## 作用
`tests/web/` 覆盖 CelestialFlow Web 层的接口与页面集成行为，确保状态快照隔离、状态拉取推送、配置推送、任务注入、错误分页过滤和前端静态资源联动保持稳定。

## 包含的测试文件
- `conftest.py`: 提供 `web_server` 和 `client` fixture。
- `test_server.py`: 覆盖快照隔离、仪表盘首页、配置 API、状态同步、任务注入及错误分页等 Web API 集成测试。

## 运行方式

```bash
pytest tests/web -v
pytest tests/web/test_server.py -v
```
