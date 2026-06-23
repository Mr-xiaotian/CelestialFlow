"""Push 路由（POST）：Reporter 推送状态、错误、结构等。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..util_cal import cal_interval
from ..util_config import save_config
from ..util_models import (
    AnalysisModel,
    ErrorsModel,
    StatusModel,
    StructureModel,
    TaskInjectionModel,
    TerminationInjectionModel,
    WebConfigModel,
)

if TYPE_CHECKING:
    from ..core_server import TaskWebServer


def register(router: APIRouter, server: TaskWebServer, config_path: str) -> None:
    """注册所有 push 路由。

    :param router: FastAPI APIRouter 实例
    :param server: TaskWebServer 实例，提供数据存储与配置
    :param config_path: 配置文件路径
    """

    # ==== Frontend Pushes ====
    @router.post("/api/push_config", response_model=None)
    async def push_config(data: WebConfigModel) -> dict[str, bool] | JSONResponse:
        """
        保存前端配置

        :param data: 前端配置数据
        :return: {"ok": True} 或 JSONResponse({"ok": False, "error": ...}, 500)
        """
        with server.config_lock:
            config_raw: Any = data.model_dump(by_alias=True)
            server.config = cast(dict[str, Any], config_raw)
            server.report_interval = cal_interval(
                int(server.config["global"]["refreshInterval"])
            )
            success: bool = save_config(server.config, config_path)
            if success:
                return {"ok": True}
            else:
                return JSONResponse(
                    content={"ok": False, "error": "Failed to save config"},
                    status_code=500,
                )

    @router.post("/api/push_injection_tasks", response_model=None)
    async def push_injection_tasks(
        data: TaskInjectionModel,
    ) -> dict[str, bool] | JSONResponse:
        """
        将前端提交的注入任务追加到待执行队列。

        :param data: 注入任务数据
        :return: {"ok": True} 或 JSONResponse({"ok": False, "msg": ...}, 500)
        """
        try:
            with server.task_injection_lock:
                for node_name, task_list in data.root.items():
                    server.injection_tasks[node_name] = task_list
            return {"ok": True}
        except Exception as e:
            return JSONResponse(
                content={"ok": False, "msg": f"任务注入失败: {e}"}, status_code=500
            )

    @router.post("/api/push_injection_terminations", response_model=None)
    async def push_injection_terminations(
        data: TerminationInjectionModel,
    ) -> dict[str, bool] | JSONResponse:
        """
        将前端提交的终止符注入目标追加到待执行集合。

        :param data: 终止符注入节点列表
        :return: {"ok": True} 或 JSONResponse({"ok": False, "msg": ...}, 500)
        """
        try:
            with server.task_injection_lock:
                for node_name in data.root:
                    server.injection_terminations.add(str(node_name))
            return {"ok": True}
        except Exception as e:
            return JSONResponse(
                content={"ok": False, "msg": f"终止符注入失败: {e}"},
                status_code=500,
            )

    # ==== Reporter / Backend Pushes ====
    @router.post("/api/push_structure")
    async def push_structure(data: StructureModel) -> dict[str, bool]:
        """
        更新图结构数据并递增版本号。

        :param data: 图结构数据
        :return: {"ok": True}
        """
        if not server.is_current_graph(data.graph_id):
            return {"ok": False}
        server.update_structure_store(data.structure)
        return {"ok": True}

    @router.post("/api/push_analysis")
    async def push_analysis(data: AnalysisModel) -> dict[str, bool]:
        """
        更新图分析信息并递增版本号。

        :param data: 图分析数据
        :return: {"ok": True}
        """
        if not server.is_current_graph(data.graph_id):
            return {"ok": False}
        server.update_analysis_store(data.analysis)
        return {"ok": True}

    @router.post("/api/push_status")
    async def push_status(data: StatusModel) -> dict[str, bool]:
        """
        更新各节点运行状态并递增版本号。

        :param data: 节点状态数据
        :return: {"ok": True}
        """
        if not server.is_current_graph(data.graph_id):
            return {"ok": False}
        server.update_status_store(float(data.timestamp), data.status)
        return {"ok": True}

    @router.post("/api/push_errors")
    async def push_errors(data: ErrorsModel) -> dict[str, bool]:
        """
        直接接收错误日志列表并存储。

        :param data: 错误内容数据
        :return: {"ok": True}
        """
        if not server.is_current_graph(data.graph_id):
            return {"ok": False}
        server.update_errors_store(
            data.errors,
        )
        return {"ok": True}
