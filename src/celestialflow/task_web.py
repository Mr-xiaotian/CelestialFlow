import os
import sys
import threading
from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import uvicorn


class StructureModel(BaseModel):
    items: List[Dict[str, Any]]


class StatusModel(BaseModel):
    status: Dict[str, dict]


class ErrorItem(BaseModel):
    timestamp: float
    node: str
    error: str
    task_id: str


class ErrorsModel(BaseModel):
    errors: List[ErrorItem]


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
    def __init__(self, host="0.0.0.0", port=5000):
        self.app = FastAPI()
        self.host = host
        self.port = port

        if os.path.isdir(static_path):
            self.app.mount("/static", StaticFiles(directory=static_path), name="static")

        self.templates = Jinja2Templates(directory=templates_path)

        # 用于存储状态、结构、错误信息
        self.status_store = {}
        self.structure_store = []
        self.error_store = []
        self.topology_store = {}
        self.pending_injection_tasks = []  # 存储前端注入任务

        self.report_interval = 5
        self._task_injection_lock = threading.Lock()

        self._setup_routes()

    def _setup_routes(self):
        app = self.app
        templates = self.templates

        @app.get("/", response_class=HTMLResponse)
        def index(request: Request):
            return templates.TemplateResponse("index.html", {"request": request})

        # ---- 展示接口 ----
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
                tasks_to_send = self.pending_injection_tasks.copy()
                self.pending_injection_tasks.clear()
            return tasks_to_send

        # ---- 接收接口 ----
        @app.post("/api/push_structure")
        async def push_structure(data: StructureModel):
            self.structure_store = data.items
            return {"ok": True}

        @app.post("/api/push_status")
        async def push_status(data: StatusModel):
            self.status_store = data.status
            return {"ok": True}

        @app.post("/api/push_errors")
        async def push_errors(data: ErrorsModel):
            self.error_store = data.errors
            return {"ok": True}

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

        @app.post("/api/push_task_injection")
        async def push_task_injection(data: TaskInjectionModel):
            try:
                print(f"[任务注入]: {data}")
                with self._task_injection_lock:
                    self.pending_injection_tasks.append(data.model_dump())
                return {"ok": True}
            except Exception as e:
                return JSONResponse(
                    content={"ok": False, "msg": f"任务注入失败: {e}"}, status_code=500
                )

        @app.route("/shutdown", methods=["POST"])
        def shutdown():
            os._exit(0)

    def start_server(self):
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")


def main_entry():
    port = 5000  # 默认端口
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"无效端口号: {sys.argv[1]}，使用默认端口 {port}")

    server = TaskWebServer(port=port)
    server.start_server()


# 运行入口
if __name__ == "__main__":
    main_entry()
