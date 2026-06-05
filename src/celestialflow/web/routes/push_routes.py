"""Push 路由（POST）：Reporter 推送状态、错误、结构等。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import partial
from typing import TYPE_CHECKING, Any, cast

from anyio.to_thread import run_sync
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...persistence.util_jsonl import load_jsonl_logs
from ..util_cal import cal_interval
from ..util_config import save_config
from ..util_models import (
    AnalysisModel,
    ErrorsContentModel,
    ErrorsMetaModel,
    StatusModel,
    StructureModel,
    TaskInjectionModel,
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

    @router.post("/api/push_config", response_model=None)
    async def push_config(data: WebConfigModel) -> dict[str, bool] | JSONResponse:
        """
        保存前端配置

        :param data: 前端配置数据
        :return: {"ok": True} 或 JSONResponse({"ok": False, "error": ...}, 500)
        """
        with server.config_lock:
            config_raw: Any = data.model_dump()
            server.config = cast(dict[str, Any], config_raw)
            server.report_interval = cal_interval(int(server.config["refreshInterval"]))
            success: bool = save_config(server.config, config_path)
            if success:
                return {"ok": True}
            else:
                return JSONResponse(
                    content={"ok": False, "error": "Failed to save config"},
                    status_code=500,
                )

    @router.post("/api/push_structure")
    async def push_structure(data: StructureModel) -> dict[str, bool]:
        """
        更新图结构数据并递增版本号。

        :param data: 图结构数据
        :return: {"ok": True}
        """
        server.update_structure_store(data.structure)
        return {"ok": True}

    @router.post("/api/push_status")
    async def push_status(data: StatusModel) -> dict[str, bool]:
        """
        更新各节点运行状态并递增版本号。

        :param data: 节点状态数据
        :return: {"ok": True}
        """
        server.update_status_store(float(data.timestamp), data.status)
        return {"ok": True}

    def _is_errors_cache_hit(rev: int, path: str) -> bool:
        return server.is_errors_cache_hit(rev, path)

    @router.post("/api/push_errors_meta")
    async def push_errors_meta(data: ErrorsMetaModel) -> dict[str, Any]:
        """
        通过 JSONL 文件路径+版本号加载错误日志；命中缓存则跳过读取。

        :param data: 错误元信息数据
        :return: {"ok": True, "cached": bool} 或 {"ok": False, "fallback": ..., ...}
        """
        # 命中缓存：path 和 rev 都没变 -> 不重新读取
        if _is_errors_cache_hit(data.rev, data.jsonl_path):
            return {"ok": True, "cached": True}

        try:
            # 不命中：更新 key 并全量加载
            run_sync_typed = cast(
                Callable[..., Awaitable[list[dict[str, Any]]]],
                run_sync,
            )
            errors = await run_sync_typed(
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
            server.update_errors_store(data.rev, data.jsonl_path, errors)
            return {"ok": True, "cached": False}
        except Exception as e:
            return {
                "ok": False,
                "fallback": "need_content",
                "reason": type(e).__name__,
                "msg": str(e),
            }

    @router.post("/api/push_errors_content")
    async def push_errors_content(data: ErrorsContentModel) -> dict[str, Any]:
        """
        直接接收错误日志列表并存储；支持增量 append；命中缓存则跳过。

        :param data: 错误内容数据
        :return: {"ok": True, "cached": bool}
        """
        if _is_errors_cache_hit(data.rev, data.jsonl_path):
            return {"ok": True, "cached": True}

        server.update_errors_store(data.rev, data.jsonl_path, data.errors)
        return {"ok": True, "cached": False}

    @router.post("/api/push_analysis")
    async def push_analysis(data: AnalysisModel) -> dict[str, bool]:
        """
        更新图分析信息并递增版本号。

        :param data: 图分析数据
        :return: {"ok": True}
        """
        server.update_analysis_store(data.analysis)
        return {"ok": True}

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
                server.injection_tasks.append(data.model_dump(mode="json"))
            return {"ok": True}
        except Exception as e:
            return JSONResponse(
                content={"ok": False, "msg": f"任务注入失败: {e}"}, status_code=500
            )
