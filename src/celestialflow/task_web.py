import anyio
import os
import threading
import uvicorn
import argparse
from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from functools import partial
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from .task_tools import load_jsonl_logs


class StructureModel(BaseModel):
    items: List[Dict[str, Any]]


class StatusModel(BaseModel):
    status: Dict[str, dict]


class ErrorsMetaModel(BaseModel):
    jsonl_path: str
    rev: int


class ErrorsContentModel(BaseModel):
    errors: list[dict]
    jsonl_path: str
    rev: int


class TopologyModel(BaseModel):
    topology: Dict[str, Any]


class IntervalModel(BaseModel):
    interval: float


class TaskInjectionModel(BaseModel):
    node: str
    task_datas: List[Any]
    timestamp: datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

static_path = os.path.join(BASE_DIR, "static")
templates_path = os.path.join(BASE_DIR, "templates")


class TaskWebServer:
    def __init__(self, host="0.0.0.0", port=5000, log_level="info"):
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
        self.topology_store = {}
        self.injection_tasks = []  # 存储前端注入任务

        self.report_interval = 5
        self._task_injection_lock = threading.Lock()

        self._errors_meta_rev: Optional[int] = None
        self._errors_meta_path: Optional[str] = None

        self._setup_routes()

    def _setup_routes(self):
        app = self.app
        templates = self.templates

        @app.get("/", response_class=HTMLResponse)
        def index(request: Request):
            return templates.TemplateResponse("index.html", {"request": request})

        # ---- 接收接口 ----
        @app.get("/api/get_structure")
        def get_structure():
            return self.structure_store

        @app.get("/api/get_status")
        def get_status():
            return self.status_store

        @app.get("/api/get_errors")
        def get_errors():
            return self.error_store

        @app.get("/api/get_topology")
        def get_topology():
            return self.topology_store

        @app.get("/api/get_interval")
        def get_interval():
            return {"interval": self.report_interval}

        @app.get("/api/get_task_injection")
        def get_task_injection():
            with self._task_injection_lock:
                tasks_to_send = self.injection_tasks.copy()
                self.injection_tasks.clear()
            return tasks_to_send

        # ---- 发送接口 ----
        @app.post("/api/push_structure")
        async def push_structure(data: StructureModel):
            self.structure_store = data.items
            return {"ok": True}

        @app.post("/api/push_status")
        async def push_status(data: StatusModel):
            self.status_store = data.status
            return {"ok": True}

        @app.post("/api/push_errors_meta")
        async def push_errors_meta(data: ErrorsMetaModel):
            # 命中缓存：path 和 rev 都没变 -> 不重新读取
            if (
                data.jsonl_path == self._errors_meta_path
                and data.rev == self._errors_meta_rev
            ):
                return {"ok": True, "cached": True}

            try:
                # 不命中：更新 key 并全量加载
                self.error_store = await anyio.to_thread.run_sync(
                    partial(
                        load_jsonl_logs,
                        path=data.jsonl_path,
                        keys=["ts", "error_id", "error_repr", "stage", "task_repr"],
                    )
                )
                self._errors_meta_path = data.jsonl_path
                self._errors_meta_rev = data.rev
                return {"ok": True, "cached": False}
            except Exception as e:
                return {"ok": False, "fallback": "need_content", "reason": type(e).__name__, "msg": str(e)}
            
        @app.post("/api/push_errors_content")
        async def push_errors_content(data: ErrorsContentModel):
            # 命中缓存：path 和 rev 都没变 -> 不重新读取
            if (
                data.jsonl_path == self._errors_meta_path
                and data.rev == self._errors_meta_rev
            ):
                return {"ok": True, "cached": True}
            
            try:
                self.error_store = data.errors
                self._errors_meta_path = data.jsonl_path
                self._errors_meta_rev = data.rev
                return {"ok": True, "cached": False}
            except Exception as e:
                return {"ok": False, "fallback": "none", "reason": type(e).__name__, "msg": str(e)}

        @app.post("/api/push_topology")
        async def push_topology(data: TopologyModel):
            self.topology_store = data.topology
            return {"ok": True}

        @app.post("/api/push_interval")
        async def push_interval(data: IntervalModel):
            try:
                self.report_interval = max(1.0, min(data.interval / 1000.0, 60.0))
                return {"message": "Interval updated"}
            except Exception as e:
                return JSONResponse(content={"error": str(e)}, status_code=400)

        @app.post("/api/push_injection_tasks")
        async def push_injection_tasks(data: TaskInjectionModel):
            try:
                with self._task_injection_lock:
                    self.injection_tasks.append(data.model_dump())
                return {"ok": True}
            except Exception as e:
                return JSONResponse(
                    content={"ok": False, "msg": f"任务注入失败: {e}"}, status_code=500
                )

        @app.route("/shutdown", methods=["POST"])
        def shutdown():
            # os._exit(0)
            pass

    def start_server(self):
        uvicorn.run(self.app, host=self.host, port=self.port, log_level=self.log_level)


def parse_args():
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
