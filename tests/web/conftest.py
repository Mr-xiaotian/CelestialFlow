import pytest
from fastapi.testclient import TestClient
from celestialflow.web.core_server import TaskWebServer

@pytest.fixture
def web_server():
    # 使用默认配置初始化 server
    server = TaskWebServer()
    return server

@pytest.fixture
def client(web_server):
    # 返回 FastAPI TestClient
    return TestClient(web_server.app)
