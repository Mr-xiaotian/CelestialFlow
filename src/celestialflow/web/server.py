# web/server.py
import anyio
import os
import json
import threading
import uvicorn
import argparse
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from functools import partial
from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime

from ..persistence.util_jsonl import load_jsonl_logs


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


class TopologyModel(BaseModel):
    topology: dict[str, Any]


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
    dashboard: DashboardConfigModel
    cards: dict[str, CardConfigModel]


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

static_path = os.path.join(BASE_DIR, "static")
templates_path = os.path.join(BASE_DIR, "templates")


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"config file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return WebConfigModel.model_validate(data).model_dump()


def save_config(config: dict) -> bool:
    """Save configuration to JSON file."""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error: Failed to save config: {e}")
        return False
    

def cal_interval(refresh_interval: int) -> float:
    return max(1.0, min(float(refresh_interval) / 1000.0, 60.0))


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
        self.summary_store = {}
        self.history_store = {}
        self.injection_tasks = []  # 存储前端注入任务

        self._task_injection_lock = threading.Lock()

        self._errors_meta_rev: Optional[int] = None
        self._errors_meta_path: Optional[str] = None

        # 加载配置
        self.config = load_config()
        self.report_interval = cal_interval(self.config["refreshInterval"])
        self._config_lock = threading.Lock()

        self._setup_routes()

    def _setup_routes(self):
        app = self.app
        templates = self.templates

        @app.get("/", response_class=HTMLResponse)
        def index(request: Request):
            return templates.TemplateResponse("index.html", {"request": request})


        # ---- 接收接口 ----
        @app.get("/api/pull_config")
        def pull_config():
            """获取前端配置"""
            with self._config_lock:
                return self.config
            
        @app.get("/api/pull_structure")
        def pull_structure():
            return self.structure_store

        @app.get("/api/pull_status")
        def pull_status():
            return self.status_store

        @app.get("/api/pull_errors")
        def pull_errors():
            return self.error_store

        @app.get("/api/pull_topology")
        def pull_topology():
            return self.topology_store

        @app.get("/api/pull_summary")
        def pull_summary():
            return self.summary_store
        
        @app.get("/api/pull_history")
        def pull_history():
            return self.history_store

        @app.get("/api/pull_interval")
        def pull_interval():
            return {"interval": self.report_interval}

        @app.get("/api/pull_task_injection")
        def pull_task_injection():
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
                success = save_config(self.config)
                if success:
                    return {"ok": True}
                else:
                    return JSONResponse(
                        content={"ok": False, "error": "Failed to save config"},
                        status_code=500,
                    )
                
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
                return {
                    "ok": False,
                    "fallback": "need_content",
                    "reason": type(e).__name__,
                    "msg": str(e),
                }

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
                return {
                    "ok": False,
                    "fallback": "none",
                    "reason": type(e).__name__,
                    "msg": str(e),
                }

        @app.post("/api/push_topology")
        async def push_topology(data: TopologyModel):
            self.topology_store = data.topology
            return {"ok": True}

        @app.post("/api/push_summary")
        async def push_summary(data: SummaryModel):
            self.summary_store = data.summary
            return {"ok": True}
        
        @app.post("/api/push_history")
        async def push_history(data: HistoryModel):
            self.history_store = data.history
            return {"ok": True}

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
