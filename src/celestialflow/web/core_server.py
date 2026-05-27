# web/core_server.py
from __future__ import annotations

import argparse
import os
import threading
from typing import Any, cast

import uvicorn  # type: ignore[reportMissingImports]
from fastapi import (  # type: ignore[reportMissingImports, reportUnknownVariableType]
    FastAPI,
)
from fastapi.staticfiles import (
    StaticFiles,  # type: ignore[reportMissingImports, reportUnknownVariableType]
)
from fastapi.templating import (
    Jinja2Templates,  # type: ignore[reportMissingImports, reportUnknownVariableType]
)

from .routes import create_router
from .util_cal import cal_interval
from .util_config import load_config
from .util_models import WebConfigModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

static_path = os.path.join(BASE_DIR, "static")
templates_path = os.path.join(BASE_DIR, "templates")


class TaskWebServer:
    """FastAPI Web 服务，提供任务可视化、状态推送和任务注入接口。"""

    def __init__(
        self, host: str = "0.0.0.0", port: int = 5000, log_level: str = "info"
    ) -> None:
        """
        初始化 FastAPI 应用、数据存储、版本计数器及路由。

        :param host: 绑定主机地址，默认 "0.0.0.0"
        :param port: 绑定端口，默认 5000
        :param log_level: uvicorn 日志级别，默认 "info"
        """
        self.app: FastAPI = FastAPI()  # type: ignore[reportUnknownMemberType]
        self.host: str = host
        self.port: int = port
        self.log_level: str = log_level

        if os.path.isdir(static_path):
            self.app.mount("/static", StaticFiles(directory=static_path), name="static")  # type: ignore[reportUnknownMemberType]

        self.templates: Jinja2Templates = Jinja2Templates(directory=templates_path)  # type: ignore[reportUnknownMemberType]

        # 用于存储状态、结构、错误信息
        self.status_store: dict[str, dict[str, Any]] = {}
        self.status_timestamp: float = 0.0
        self.structure_store: list[dict[str, Any]] = []
        self.error_store: list[dict[str, Any]] = []
        self.analysis_store: dict[str, Any] = {}
        self.summary_store: dict[str, Any] = {}
        self.injection_tasks: list[dict[str, Any]] = []  # 存储前端注入任务

        # 用于存储任务注入锁
        self.task_injection_lock: threading.Lock = threading.Lock()

        self.errors_meta_rev: int | None = None
        self.errors_meta_path: str | None = None

        # 每次 push 时递增，pull 时对比，无变化则返回 null data
        self.store_revs: dict[str, int] = {
            "status": 0,
            "structure": 0,
            "errors": 0,
            "analysis": 0,
            "summary": 0,
        }

        # 加载配置
        config_raw: Any = WebConfigModel.model_validate(  # type: ignore[reportUnknownMemberType]
            load_config(CONFIG_PATH)
        ).model_dump()  # type: ignore[reportUnknownMemberType]
        self.config: dict[str, Any] = cast(dict[str, Any], config_raw)
        self.report_interval: float = cal_interval(int(self.config["refreshInterval"]))
        self.config_lock: threading.Lock = threading.Lock()
        self.config_path: str = CONFIG_PATH

        self._setup_routes()

    def _setup_routes(self) -> None:
        """注册所有 HTTP 路由（页面入口、pull 接口、push 接口）。"""
        self.app.include_router(create_router(self))

    def start_server(self) -> None:
        """启动 uvicorn 服务，阻塞直到服务停止。"""
        uvicorn.run(self.app, host=self.host, port=self.port, log_level=self.log_level)  # type: ignore[reportUnknownMemberType]


def parse_args() -> argparse.Namespace:
    """解析命令行参数：--host、--port、--log-level。"""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="task-web",
        description="CelestialFlow Task Web Monitor Server",
    )

    _ = parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind host (default: 0.0.0.0)",
    )

    _ = parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Bind port (default: 5000)",
    )

    _ = parser.add_argument(
        "--log-level",
        default="info",
        type=lambda s: s.lower(),
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Uvicorn log level",
    )

    return parser.parse_args()


def main_entry() -> None:
    """CLI 入口：解析参数并启动 TaskWebServer。"""
    args: argparse.Namespace = parse_args()

    server: TaskWebServer = TaskWebServer(
        host=cast(str, args.host),
        port=cast(int, args.port),
        log_level=cast(str, args.log_level),
    )

    server.start_server()


# 运行入口
if __name__ == "__main__":
    main_entry()
