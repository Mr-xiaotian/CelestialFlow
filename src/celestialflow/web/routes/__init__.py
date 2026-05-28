"""路由组装入口。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from . import pull_routes, push_routes

if TYPE_CHECKING:
    from ..core_server import TaskWebServer


def create_router(server: TaskWebServer) -> APIRouter:
    """创建并注册所有路由的 APIRouter。

    :param server: TaskWebServer 实例，路由需持有其状态引用
    :return: 组装完成的 APIRouter 实例
    """
    router = APIRouter()

    # 页面入口
    @router.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        return server.templates.TemplateResponse(request=request, name="index.html")

    # 子模块路由
    pull_routes.register(router, server)
    push_routes.register(router, server, server.config_path)

    return router
