# web/core_server.py
import argparse
import os
import threading
from datetime import datetime
from functools import partial
from typing import Any, Optional

import anyio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ..persistence.util_jsonl import load_jsonl_logs
from .util_cal import cal_interval
from .util_config import load_config, save_config
from .util_error import filter_errors, normalize_errors_query, paginate_errors


class StructureModel(BaseModel):
    items: list[dict[str, Any]]


class StatusModel(BaseModel):
    status: dict[str, dict]


class ErrorsMetaModel(BaseModel):
    jsonl_path: str
    rev: int


class ErrorsContentModel(BaseModel):
    errors: list[dict]
    jsonl_path: str
    rev: int


class AnalysisModel(BaseModel):
    analysis: dict[str, Any]


class SummaryModel(BaseModel):
    summary: dict[str, Any]


class HistoryModel(BaseModel):
    history: dict[str, list[dict]]


class IntervalModel(BaseModel):
    interval: float


class TaskInjectionModel(BaseModel):
    node: str
    task_datas: list[Any]
    timestamp: datetime


class CardConfigModel(BaseModel):
    title: str


class DashboardConfigModel(BaseModel):
    left: list[str]
    middle: list[str]
    right: list[str]


class WebConfigModel(BaseModel):
    theme: str
    refreshInterval: int
    historyLimit: int
    dashboard: DashboardConfigModel
    cards: dict[str, CardConfigModel]


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

static_path = os.path.join(BASE_DIR, "static")
templates_path = os.path.join(BASE_DIR, "templates")


class TaskWebServer:
    def __init__(self, host="0.0.0.0", port=5000, log_level="info"):
        """初始化 FastAPI 应用、数据存储、版本计数器及路由。"""
        self.app = FastAPI()
        self.host = host
        self.port = port
        self.log_level = log_level

        if os.path.isdir(static_path):
            self.app.mount("/static", StaticFiles(directory=static_path), name="static")

        self.templates = Jinja2Templates(directory=templates_path)

        # 用于存储状态、结构、错误信息
        self.status_store = {}
        self.structure_store = []
        self.error_store = []
        self.analysis_store = {}
        self.summary_store = {}
        self.history_store = {}
        self.injection_tasks = []  # 存储前端注入任务

        # 用于存储任务注入锁
        self._task_injection_lock = threading.Lock()

        self._errors_meta_rev: Optional[int] = None
        self._errors_meta_path: Optional[str] = None

        # 每次 push 时递增，pull 时对比，无变化则返回 null data
        self._store_revs: dict[str, int] = {
            "status": 0,
            "structure": 0,
            "errors": 0,
            "analysis": 0,
            "summary": 0,
            "history": 0,
        }

        # 加载配置
        self.config = WebConfigModel.model_validate(
            load_config(CONFIG_PATH)
        ).model_dump()
        self.report_interval = cal_interval(self.config["refreshInterval"])
        self.history_limit = self.config.get("historyLimit", 20)
        self._config_lock = threading.Lock()

        self._setup_routes()

    def _setup_routes(self):
        """注册所有 HTTP 路由（页面入口、pull 接口、push 接口）。"""
        app = self.app
        templates = self.templates

        @app.get("/", response_class=HTMLResponse)
        def index(request: Request):
            """返回主页面 HTML。"""
            return templates.TemplateResponse(request=request, name="index.html")

        # ---- 接收接口 ----
        @app.get("/api/pull_config")
        def pull_config():
            """获取前端配置"""
            with self._config_lock:
                return self.config

        @app.get("/api/pull_structure")
        def pull_structure(known_rev: int = -1):
            """返回图结构数据；若版本未变则返回 data=null。"""
            rev = self._store_revs["structure"]
            if known_rev == rev:
                return {"rev": rev, "data": None}
            return {"rev": rev, "data": self.structure_store}

        @app.get("/api/pull_status")
        def pull_status(known_rev: int = -1):
            """返回各节点运行状态；若版本未变则返回 data=null。"""
            rev = self._store_revs["status"]
            if known_rev == rev:
                return {"rev": rev, "data": None}
            return {"rev": rev, "data": self.status_store}

        @app.get("/api/pull_errors")
        def pull_errors(
            known_rev: int = -1,
            page: int = 1,
            page_size: int = 10,
            node: str = "",
            keyword: str = "",
        ):
            """返回错误日志分页数据；若版本未变则返回 data=null。"""
            rev = self._store_revs["errors"]
            (
                normalized_page,
                normalized_page_size,
                normalized_node,
                normalized_keyword,
            ) = normalize_errors_query(page, page_size, node, keyword)
            filtered = filter_errors(
                self.error_store,
                normalized_node,
                normalized_keyword,
            )
            total, total_pages, page_items = paginate_errors(
                filtered,
                normalized_page,
                normalized_page_size,
            )
            normalized_page = min(normalized_page, total_pages)

            if known_rev == rev:
                return {
                    "rev": rev,
                    "page": normalized_page,
                    "page_size": normalized_page_size,
                    "total": total,
                    "total_pages": total_pages,
                    "data": None,
                }

            return {
                "rev": rev,
                "page": normalized_page,
                "page_size": normalized_page_size,
                "total": total,
                "total_pages": total_pages,
                "data": page_items,
            }

        @app.get("/api/pull_analysis")
        def pull_analysis(known_rev: int = -1):
            """返回图拓扑信息；若版本未变则返回 data=null。"""
            rev = self._store_revs["analysis"]
            if known_rev == rev:
                return {"rev": rev, "data": None}
            return {"rev": rev, "data": self.analysis_store}

        @app.get("/api/pull_summary")
        def pull_summary(known_rev: int = -1):
            """返回全局任务汇总数据；若版本未变则返回 data=null。"""
            rev = self._store_revs["summary"]
            if known_rev == rev:
                return {"rev": rev, "data": None}
            return {"rev": rev, "data": self.summary_store}

        @app.get("/api/pull_history")
        def pull_history(known_rev: int = -1):
            """返回节点历史走势数据；若版本未变则返回 data=null。"""
            rev = self._store_revs["history"]
            if known_rev == rev:
                return {"rev": rev, "data": None}
            return {"rev": rev, "data": self.history_store}

        @app.get("/api/pull_interval")
        def pull_interval():
            """返回当前轮询间隔（秒）。"""
            return {"interval": self.report_interval}

        @app.get("/api/pull_history_limit")
        def pull_history_limit():
            """返回历史记录最大保留条数。"""
            return {"historyLimit": self.history_limit}

        @app.get("/api/pull_task_injection")
        def pull_task_injection():
            """取出并清空待执行的前端注入任务列表。"""
            with self._task_injection_lock:
                tasks_to_send = self.injection_tasks.copy()
                self.injection_tasks.clear()
            return tasks_to_send

        # ---- 发送接口 ----
        @app.post("/api/push_config")
        async def push_config(data: WebConfigModel):
            """保存前端配置"""
            with self._config_lock:
                self.config = data.model_dump()
                self.report_interval = cal_interval(self.config["refreshInterval"])
                self.history_limit = self.config.get("historyLimit", 20)
                success = save_config(self.config, CONFIG_PATH)
                if success:
                    return {"ok": True}
                else:
                    return JSONResponse(
                        content={"ok": False, "error": "Failed to save config"},
                        status_code=500,
                    )

        @app.post("/api/push_structure")
        async def push_structure(data: StructureModel):
            """更新图结构数据并递增版本号。"""
            self.structure_store = data.items
            self._store_revs["structure"] += 1
            return {"ok": True}

        @app.post("/api/push_status")
        async def push_status(data: StatusModel):
            """更新各节点运行状态并递增版本号。"""
            self.status_store = data.status
            self._store_revs["status"] += 1
            return {"ok": True}

        @app.post("/api/push_errors_meta")
        async def push_errors_meta(data: ErrorsMetaModel):
            """通过 JSONL 文件路径+版本号加载错误日志；命中缓存则跳过读取。"""
            # 命中缓存：path 和 rev 都没变 -> 不重新读取
            if (
                data.rev == self._errors_meta_rev
                and data.jsonl_path == self._errors_meta_path
            ):
                return {"ok": True, "cached": True}

            try:
                # 不命中：更新 key 并全量加载
                self.error_store = await anyio.to_thread.run_sync(
                    partial(
                        load_jsonl_logs,
                        path=data.jsonl_path,
                        keys=[
                            "ts",
                            "error_id",
                            "error_repr",
                            "error",
                            "stage",
                            "task_repr",
                        ],
                    )
                )
                self._errors_meta_rev = data.rev
                self._errors_meta_path = data.jsonl_path
                self._store_revs["errors"] += 1
                return {"ok": True, "cached": False}
            except Exception as e:
                return {
                    "ok": False,
                    "fallback": "need_content",
                    "reason": type(e).__name__,
                    "msg": str(e),
                }

        @app.post("/api/push_errors_content")
        async def push_errors_content(data: ErrorsContentModel):
            """直接接收错误日志列表并存储；支持增量 append（offset > 0）；命中缓存则跳过。"""
            if (
                data.rev == self._errors_meta_rev
                and data.jsonl_path == self._errors_meta_path
            ):
                return {"ok": True, "cached": True}

            self.error_store = data.errors

            self._errors_meta_rev = data.rev
            self._errors_meta_path = data.jsonl_path
            self._store_revs["errors"] += 1
            return {"ok": True, "cached": False}

        @app.post("/api/push_analysis")
        async def push_analysis(data: AnalysisModel):
            """更新图分析信息并递增版本号。"""
            self.analysis_store = data.analysis
            self._store_revs["analysis"] += 1
            return {"ok": True}

        @app.post("/api/push_summary")
        async def push_summary(data: SummaryModel):
            """更新全局任务汇总数据并递增版本号。"""
            self.summary_store = data.summary
            self._store_revs["summary"] += 1
            return {"ok": True}

        @app.post("/api/push_history")
        async def push_history(data: HistoryModel):
            """更新节点历史走势数据并递增版本号。"""
            self.history_store = data.history
            self._store_revs["history"] += 1
            return {"ok": True}

        @app.post("/api/push_injection_tasks")
        async def push_injection_tasks(data: TaskInjectionModel):
            """将前端提交的注入任务追加到待执行队列。"""
            try:
                with self._task_injection_lock:
                    self.injection_tasks.append(data.model_dump(mode="json"))
                return {"ok": True}
            except Exception as e:
                return JSONResponse(
                    content={"ok": False, "msg": f"任务注入失败: {e}"}, status_code=500
                )

    def start_server(self):
        """启动 uvicorn 服务，阻塞直到服务停止。"""
        uvicorn.run(self.app, host=self.host, port=self.port, log_level=self.log_level)


def parse_args():
    """解析命令行参数：--host、--port、--log-level。"""
    parser = argparse.ArgumentParser(
        prog="task-web",
        description="CelestialFlow Task Web Monitor Server",
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind host (default: 0.0.0.0)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Bind port (default: 5000)",
    )

    parser.add_argument(
        "--log-level",
        default="info",
        type=lambda s: s.lower(),
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Uvicorn log level",
    )

    return parser.parse_args()


def main_entry():
    """CLI 入口：解析参数并启动 TaskWebServer。"""
    args = parse_args()

    server = TaskWebServer(
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )

    server.start_server()


# 运行入口
if __name__ == "__main__":
    main_entry()
