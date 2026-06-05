# web 测试包

> 最后更新日期: 2026/06/05

## 作用
`tests/web/` 覆盖 CelestialFlow Web 层的接口与页面集成行为，确保状态拉取、配置推送、结构展示和前端静态资源联动保持稳定。

## 包含的测试文件
- `test_routes.py`: Web API 路由与请求返回值。
- `test_server.py`: Web 服务端启动与集成行为。

## 运行方式

```bash
pytest tests/web -v
pytest tests/web -k "routes or server" -v
```
