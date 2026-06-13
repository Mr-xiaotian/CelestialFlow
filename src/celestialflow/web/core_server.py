# web/core_server.py
from __future__ import annotations

import argparse
import copy
import os
import tempfile
import threading
from typing import Any, cast

import uvicorn
from fastapi import (
    FastAPI,
)
from fastapi.staticfiles import (
    StaticFiles,
)
from fastapi.templating import (
    Jinja2Templates,
)

from ..persistence.util_sqlite import (
    connect_errors_db,
    load_error_records,
    query_error_records,
    replace_error_records,
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
        self.app: FastAPI = FastAPI()
        self.host: str = host
        self.port: int = port
        self.log_level: str = log_level

        if os.path.isdir(static_path):
            self.app.mount("/static", StaticFiles(directory=static_path), name="static")

        self.templates: Jinja2Templates = Jinja2Templates(directory=templates_path)

        # 用于存储状态、结构、错误信息
        self.status_store: dict[str, dict[str, Any]] = {}
        self.status_timestamp: float = 0.0
        self.structure_store: dict[str, Any] = {
            "nodes": {},
            "edges": {},
            "source_nodes": [],
        }
        self.analysis_store: dict[str, Any] = {}
        self.summary_store: dict[str, Any] = {}
        self.injection_tasks: dict[str, list[Any]] = {}  # 存储前端注入任务
        fd, errors_db_path = tempfile.mkstemp(
            prefix="celestialflow-web-errors-", suffix=".sqlite3"
        )
        os.close(fd)
        self.errors_db_path: str = errors_db_path
        conn = connect_errors_db(self.errors_db_path)
        conn.close()

        # 各类 store 的 rev + payload 需要原子读写，避免 pull 读到撕裂快照
        self.status_lock: threading.Lock = threading.Lock()
        self.structure_lock: threading.Lock = threading.Lock()
        self.errors_lock: threading.Lock = threading.Lock()
        self.analysis_lock: threading.Lock = threading.Lock()

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
        config_raw: Any = WebConfigModel.model_validate(
            load_config(CONFIG_PATH)
        ).model_dump(by_alias=True)
        self.config: dict[str, Any] = cast(dict[str, Any], config_raw)
        self.report_interval: float = cal_interval(
            int(self.config["global"]["refreshInterval"])
        )
        self.config_lock: threading.Lock = threading.Lock()
        self.config_path: str = CONFIG_PATH

        self._setup_routes()

    # ==== Store Snapshot ====
    def update_structure_store(self, structure: dict[str, Any]) -> None:
        """原子更新结构数据及其版本号。"""
        with self.structure_lock:
            self.structure_store = copy.deepcopy(structure)
            self.store_revs["structure"] += 1

    def get_structure_snapshot(self) -> tuple[int, dict[str, Any]]:
        """原子读取结构数据快照。"""
        with self.structure_lock:
            return self.store_revs["structure"], copy.deepcopy(self.structure_store)

    def update_status_store(
        self, timestamp: float, status: dict[str, dict[str, Any]]
    ) -> None:
        """原子更新状态数据、时间戳及其版本号。"""
        with self.status_lock:
            self.status_timestamp = timestamp
            self.status_store = copy.deepcopy(status)
            self.store_revs["status"] += 1

    def get_status_snapshot(self) -> tuple[int, float, dict[str, dict[str, Any]]]:
        """原子读取状态快照。"""
        with self.status_lock:
            return (
                self.store_revs["status"],
                self.status_timestamp,
                copy.deepcopy(self.status_store),
            )

    def is_errors_cache_hit(self, rev: int, path: str) -> bool:
        """判断错误缓存是否命中。"""
        with self.errors_lock:
            return rev == self.errors_meta_rev and path == self.errors_meta_path

    def update_errors_store(
        self, rev: int, path: str, errors: list[dict[str, Any]]
    ) -> None:
        """原子更新错误缓存元信息、错误内容及其版本号。"""
        with self.errors_lock:
            replace_error_records(self.errors_db_path, errors)
            self.errors_meta_rev = rev
            self.errors_meta_path = path
            self.store_revs["errors"] += 1

    def get_errors_snapshot(self) -> tuple[int, list[dict[str, Any]]]:
        """原子读取错误数据快照。"""
        with self.errors_lock:
            return self.store_revs["errors"], load_error_records(self.errors_db_path)

    def query_errors(
        self,
        page: int,
        page_size: int,
        node: str,
        keyword: str,
        sort_order: str,
    ) -> tuple[int, int, list[dict[str, Any]]]:
        """原子查询错误数据分页结果。"""
        with self.errors_lock:
            return query_error_records(
                self.errors_db_path, page, page_size, node, keyword, sort_order
            )

    def update_analysis_store(self, analysis: dict[str, Any]) -> None:
        """原子更新图分析数据及其版本号。"""
        with self.analysis_lock:
            self.analysis_store = copy.deepcopy(analysis)
            self.store_revs["analysis"] += 1

    def get_analysis_snapshot(self) -> tuple[int, dict[str, Any]]:
        """原子读取图分析快照。"""
        with self.analysis_lock:
            return self.store_revs["analysis"], copy.deepcopy(self.analysis_store)

    def _setup_routes(self) -> None:
        """注册所有 HTTP 路由（页面入口、pull 接口、push 接口）。"""
        self.app.include_router(create_router(self))

    def start_server(self) -> None:
        """启动 uvicorn 服务，阻塞直到服务停止。"""
        uvicorn.run(self.app, host=self.host, port=self.port, log_level=self.log_level)


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
