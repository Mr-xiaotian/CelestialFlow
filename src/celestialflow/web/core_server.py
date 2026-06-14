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
    append_error_records,
    connect_errors_db,
    get_max_error_row_id,
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
        self.current_graph_id: str = ""
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
        self.graph_context_lock: threading.Lock = threading.Lock()

        # 用于存储任务注入锁
        self.task_injection_lock: threading.Lock = threading.Lock()

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

    # ==== Graph Context ====
    def _reset_graph_scoped_stores(self) -> None:
        """
        清空与当前 graph 运行实例绑定的缓存。

        该方法会同时重置状态、结构、分析与错误缓存，并递增对应的
        store 版本号，使前端在下一轮 pull 时感知到 graph 已切换。

        :return: None
        """
        with self.status_lock:
            self.status_store = {}
            self.status_timestamp = 0.0
            self.store_revs["status"] += 1
        with self.structure_lock:
            self.structure_store = {
                "nodes": {},
                "edges": {},
                "source_nodes": [],
            }
            self.store_revs["structure"] += 1
        with self.analysis_lock:
            self.analysis_store = {}
            self.store_revs["analysis"] += 1
        with self.errors_lock:
            replace_error_records(self.errors_db_path, [])
            self.store_revs["errors"] += 1

    def sync_graph_context(self, graph_id: str) -> bool:
        """
        同步 server 当前持有的 graph 上下文。

        当传入的 ``graph_id`` 为空时不做任何事；当其与当前 graph 不一致时，
        server 会切换到新的 graph，并清空所有 graph 级缓存。

        :param graph_id: reporter 当前任务图实例的唯一标识
        :return: 在调用前 server 是否已经持有当前 graph
        :rtype: bool
        """
        with self.graph_context_lock:
            if self.current_graph_id == graph_id:
                return True
            if not graph_id:
                return False
            if not self.current_graph_id:
                self.current_graph_id = graph_id
                return False
            self.current_graph_id = graph_id
            self._reset_graph_scoped_stores()
            return False

    def is_current_graph(self, graph_id: str) -> bool:
        """
        判断给定 ``graph_id`` 是否等于 server 当前 graph 上下文。

        该方法只做一致性检查，不会修改任何缓存或 graph 上下文。

        :param graph_id: 待校验的任务图实例标识
        :return: 是否为当前 graph
        :rtype: bool
        """
        if not graph_id:
            return False
        with self.graph_context_lock:
            return bool(self.current_graph_id) and self.current_graph_id == graph_id

    # ==== Store Writes ====
    def update_structure_store(self, structure: dict[str, Any]) -> None:
        """
        原子更新结构缓存及其版本号。

        :param structure: 最新任务图结构数据
        :return: None
        """
        with self.structure_lock:
            self.structure_store = copy.deepcopy(structure)
            self.store_revs["structure"] += 1

    def update_status_store(
        self, timestamp: float, status: dict[str, dict[str, Any]]
    ) -> None:
        """
        原子更新状态缓存、时间戳及其版本号。

        :param timestamp: 当前状态快照对应的统一时间戳
        :param status: 各节点状态字典
        :return: None
        """
        with self.status_lock:
            self.status_timestamp = timestamp
            self.status_store = copy.deepcopy(status)
            self.store_revs["status"] += 1

    def update_errors_store(
        self,
        errors: list[dict[str, Any]],
        *,
        append: bool = False,
    ) -> None:
        """
        原子更新错误缓存及其版本号。

        当 ``append`` 为 ``True`` 时，只向现有 sqlite 错误缓存追加新错误；
        否则将以给定错误列表整体替换当前缓存。

        :param errors: 待写入的错误记录列表
        :param append: 是否以追加模式写入，默认 ``False``
        :return: None
        """
        with self.errors_lock:
            if append:
                _ = append_error_records(self.errors_db_path, errors)
            else:
                replace_error_records(self.errors_db_path, errors)
            self.store_revs["errors"] += 1

    def update_analysis_store(self, analysis: dict[str, Any]) -> None:
        """
        原子更新图分析缓存及其版本号。

        :param analysis: 最新图分析数据
        :return: None
        """
        with self.analysis_lock:
            self.analysis_store = copy.deepcopy(analysis)
            self.store_revs["analysis"] += 1

    # ==== Store Reads ====
    def get_structure_snapshot(self) -> tuple[int, dict[str, Any]]:
        """
        原子读取结构缓存快照。

        :return: ``(rev, structure_store)``
        :rtype: tuple[int, dict[str, Any]]
        """
        with self.structure_lock:
            return self.store_revs["structure"], copy.deepcopy(self.structure_store)

    def get_config(self) -> dict[str, Any]:
        """
        读取前端配置。

        :return: 前端配置字典
        :rtype: dict[str, Any]
        """
        with self.config_lock:
            return self.config

    def get_status_snapshot(self) -> tuple[int, float, dict[str, dict[str, Any]]]:
        """
        原子读取状态缓存快照。

        :return: ``(rev, timestamp, status_store)``
        :rtype: tuple[int, float, dict[str, dict[str, Any]]]
        """
        with self.status_lock:
            return (
                self.store_revs["status"],
                self.status_timestamp,
                copy.deepcopy(self.status_store),
            )

    def get_errors_snapshot(self) -> tuple[int, list[dict[str, Any]]]:
        """
        原子读取错误缓存快照。

        :return: ``(rev, errors)``
        :rtype: tuple[int, list[dict[str, Any]]]
        """
        with self.errors_lock:
            return self.store_revs["errors"], load_error_records(self.errors_db_path)

    def get_server_state(self, graph_id: str = "") -> dict[str, Any]:
        """
        读取 reporter 同步决策所需的服务端状态。

        如果调用方传入 ``graph_id``，server 会先同步 graph 上下文，再返回
        当前 graph 对应的结构、分析和错误缓存摘要。

        :param graph_id: reporter 当前任务图实例的唯一标识，默认空字符串
        :return: 服务端同步状态摘要字典
        :rtype: dict[str, Any]
        """
        is_current_graph = self.sync_graph_context(graph_id)
        with self.structure_lock:
            has_structure = bool(
                self.structure_store["nodes"]
                or self.structure_store["edges"]
                or self.structure_store["source_nodes"]
            )
        with self.analysis_lock:
            has_analysis = bool(self.analysis_store)
        return {
            "interval": self.report_interval,
            "is_current_graph": is_current_graph,
            "has_structure": has_structure,
            "has_analysis": has_analysis,
            "max_error_row_id": self.get_max_error_row_id(),
        }
    
    def get_injection_tasks(self) -> dict[str, list[Any]]:
        with self.task_injection_lock:
            tasks = self.injection_tasks.copy()
            self.injection_tasks = {}
            return tasks

    def get_errors_rev(self) -> int:
        """
        原子读取错误缓存版本号。

        :return: 当前错误缓存版本号
        :rtype: int
        """
        with self.errors_lock:
            return self.store_revs["errors"]

    def get_errors(
        self,
        page: int,
        page_size: int,
        node: str,
        keyword: str,
        sort_order: str,
    ) -> tuple[int, int, list[dict[str, Any]]]:
        """
        原子查询错误缓存的分页结果。

        :param page: 请求页码
        :param page_size: 每页大小
        :param node: 节点名称过滤条件
        :param keyword: 关键词过滤条件
        :param sort_order: 排序方式，支持 ``newest`` 或 ``oldest``
        :return: ``(total, total_pages, page_items)``
        :rtype: tuple[int, int, list[dict[str, Any]]]
        """
        with self.errors_lock:
            return query_error_records(
                self.errors_db_path, page, page_size, node, keyword, sort_order
            )

    def get_max_error_row_id(self) -> int:
        """
        原子读取当前错误缓存中的最大错误行号。

        :return: 当前缓存中最大的错误 row id
        :rtype: int
        """
        with self.errors_lock:
            return get_max_error_row_id(self.errors_db_path)

    def get_analysis_snapshot(self) -> tuple[int, dict[str, Any]]:
        """
        原子读取图分析缓存快照。

        :return: ``(rev, analysis_store)``
        :rtype: tuple[int, dict[str, Any]]
        """
        with self.analysis_lock:
            return self.store_revs["analysis"], copy.deepcopy(self.analysis_store)

    # ==== Application Lifecycle ====
    def _setup_routes(self) -> None:
        """
        注册所有 HTTP 路由。

        :return: None
        """
        self.app.include_router(create_router(self))

    def start_server(self) -> None:
        """
        启动 uvicorn 服务并阻塞到进程退出。

        :return: None
        """
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
