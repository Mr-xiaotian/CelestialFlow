"""Pull 路由（GET）：客户端拉取状态、结构、配置等。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter

from ..util_error import filter_errors, normalize_errors_query, paginate_errors

if TYPE_CHECKING:
    from ..core_server import TaskWebServer


def register(router: APIRouter, server: TaskWebServer) -> None:
    """注册所有 pull 路由。

    :param router: FastAPI APIRouter 实例
    :param server: TaskWebServer 实例，提供数据存储与配置
    """

    @router.get("/api/pull_config")
    def pull_config() -> dict[str, Any]:
        """获取前端配置

        :return: 前端配置字典
        """
        with server.config_lock:
            return server.config

    @router.get("/api/pull_structure")
    def pull_structure(known_rev: int = -1) -> dict[str, Any]:
        """
        返回图结构数据；若版本未变则返回 data=null。

        :param known_rev: 客户端已知的版本号
        :return: {"rev": int, "data": list | None}
        """
        rev: int = server.store_revs["structure"]
        if known_rev == rev:
            return {"rev": rev, "data": None}
        return {"rev": rev, "data": server.structure_store}

    @router.get("/api/pull_status")
    def pull_status(known_rev: int = -1) -> dict[str, Any]:
        """
        返回各节点运行状态；若版本未变则返回 data=null。

        :param known_rev: 客户端已知的版本号
        :return: {"rev": int, "timestamp": float, "data": dict | None}
        """
        rev: int = server.store_revs["status"]
        if known_rev == rev:
            return {"rev": rev, "timestamp": server.status_timestamp, "data": None}
        return {
            "rev": rev,
            "timestamp": server.status_timestamp,
            "data": server.status_store,
        }

    @router.get("/api/pull_errors")
    def pull_errors(
        known_rev: int = -1,
        page: int = 1,
        page_size: int = 10,
        node: str = "",
        keyword: str = "",
    ) -> dict[str, Any]:
        """
        返回错误日志分页数据；若版本未变则返回 data=null。

        :param known_rev: 客户端已知的版本号，默认 -1
        :param page: 页码，默认 1
        :param page_size: 每页大小，默认 10
        :param node: 节点名称过滤，默认 ""
        :param keyword: 关键词过滤，默认 ""
        :return: {"rev": int, "page": int, "page_size": int, "total": int, "total_pages": int, "data": list | None}
        """
        rev: int = server.store_revs["errors"]
        (
            normalized_page,
            normalized_page_size,
            normalized_node,
            normalized_keyword,
        ) = normalize_errors_query(page, page_size, node, keyword)
        filtered = filter_errors(
            server.error_store, normalized_node, normalized_keyword
        )
        total, total_pages, page_items = paginate_errors(
            filtered, normalized_page, normalized_page_size
        )
        normalized_page = min(normalized_page, total_pages)

        base = {
            "rev": rev,
            "page": normalized_page,
            "page_size": normalized_page_size,
            "total": total,
            "total_pages": total_pages,
        }
        if known_rev == rev:
            return {**base, "data": None}
        return {**base, "data": page_items}

    @router.get("/api/pull_analysis")
    def pull_analysis(known_rev: int = -1) -> dict[str, Any]:
        """
        返回图拓扑信息；若版本未变则返回 data=null。

        :param known_rev: 客户端已知的版本号
        :return: {"rev": int, "data": dict | None}
        """
        rev: int = server.store_revs["analysis"]
        if known_rev == rev:
            return {"rev": rev, "data": None}
        return {"rev": rev, "data": server.analysis_store}

    @router.get("/api/pull_summary")
    def pull_summary(known_rev: int = -1) -> dict[str, Any]:
        """
        返回全局任务汇总数据；若版本未变则返回 data=null。

        :param known_rev: 客户端已知的版本号
        :return: {"rev": int, "data": dict | None}
        """
        rev: int = server.store_revs["summary"]
        if known_rev == rev:
            return {"rev": rev, "data": None}
        return {"rev": rev, "data": server.summary_store}

    @router.get("/api/pull_interval")
    def pull_interval() -> dict[str, float]:
        """返回当前轮询间隔（秒）。

        :return: {"interval": float}
        """
        return {"interval": server.report_interval}

    @router.get("/api/pull_task_injection")
    def pull_task_injection() -> list[dict[str, Any]]:
        """取出并清空待执行的前端注入任务列表。

        :return: 待执行注入任务列表
        """
        with server.task_injection_lock:
            tasks = server.injection_tasks.copy()
            server.injection_tasks.clear()
        return tasks
