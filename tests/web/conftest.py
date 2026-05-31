import pytest
from fastapi.testclient import TestClient
from celestialflow.web.core_server import TaskWebServer

@pytest.fixture
def web_server():
    """创建默认配置的测试用 Web 服务器。"""
    # 使用默认配置初始化 server
    server = TaskWebServer()
    return server

@pytest.fixture
def client(web_server):
    """基于测试服务器创建 FastAPI TestClient。"""
    # 返回 FastAPI TestClient
    return TestClient(web_server.app)
