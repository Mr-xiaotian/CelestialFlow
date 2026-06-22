# Web 测试配置 (conftest.py)

> 📅 最后更新日期: 2026/05/23

## 作用
为 `tests/web` 目录下的测试用例提供 Web 服务器和 HTTP 客户端的 Pytest Fixture，模拟真实的前后端交互环境。

## 核心 Fixture
- `web_server`:
  - **功能**: 初始化一个默认配置的 `TaskWebServer` 实例。
  - **范围**: 每个测试函数运行前创建一个新实例。
- `client`:
  - **功能**: 基于 `FastAPI.testclient.TestClient` 创建一个同步 HTTP 客户端。
  - **依赖**: 依赖于 `web_server` fixture，直接访问其内部的 `app` 实例。

## 使用示例
```python
def test_api(client):
    response = client.get("/api/endpoint")
    assert response.status_code == 200
```

## 注意事项
- 测试使用的是 FastAPI 内置的 TestClient，不会真实启动端口监听，执行效率高且无端口冲突风险。
- 相关实现位于 `src/celestialflow/web/core_server.py`。
