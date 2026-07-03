"""Pull 路由（GET）：客户端拉取状态、结构、配置等。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter

from ..util_error import normalize_errors_query

if TYPE_CHECKING:
    from ..core_server import TaskWebServer


def register(router: APIRouter, server: TaskWebServer) -> None:
    """注册所有 pull 路由。

    :param router: FastAPI APIRouter 实例
    :param server: TaskWebServer 实例，提供数据存储与配置
    """

    # ==== Reporter / Backend Pulls ====
    @router.get("/api/pull_server_state")
    def pull_server_state(graph_id: str = "") -> dict[str, Any]:
        """返回 reporter 同步决策所需的服务端状态。

        :param graph_id: reporter 当前任务图实例的唯一标识
        :return: {"interval": float, "is_current_graph": bool, "has_structure": bool, "has_analysis": bool, "max_event_id_in_fail": int | None}
        """
        return server.get_server_state(graph_id)

    @router.get("/api/pull_injection")
    def pull_injection() -> dict[str, Any]:
        """取出并清空待执行的前端注入任务与终止符。

        :return: ``{"tasks": dict[str, list[Any]], "terminations": list[str]}``
        """
        return server.get_injection()

    # ==== Frontend Pulls ====
    @router.get("/api/pull_config")
    def pull_config() -> dict[str, Any]:
        """获取前端配置

        :return: 前端配置字典
        """
        return server.get_config()

    @router.get("/api/pull_status")
    def pull_status(known_rev: int = -1) -> dict[str, Any]:
        """
        返回各节点运行状态；若版本未变则返回 data=null。

        :param known_rev: 客户端已知的版本号
        :return: {"rev": int, "timestamp": float, "data": dict | None}
        """
        rev, status_timestamp, status_store = server.get_status_snapshot()
        if known_rev == rev:
            return {"rev": rev, "timestamp": status_timestamp, "data": None}
        return {
            "rev": rev,
            "timestamp": status_timestamp,
            "data": status_store,
        }

    @router.get("/api/pull_structure")
    def pull_structure(known_rev: int = -1) -> dict[str, Any]:
        """
        返回图结构数据；若版本未变则返回 data=null。

        :param known_rev: 客户端已知的版本号
        :return: {"rev": int, "data": list | None}
        """
        rev, structure_store = server.get_structure_snapshot()
        if known_rev == rev:
            return {"rev": rev, "data": None}
        return {"rev": rev, "data": structure_store}

    @router.get("/api/pull_errors")
    def pull_errors(
        known_rev: int = -1,
        page: int = 1,
        page_size: int = 10,
        node: str = "",
        keyword: str = "",
        sort_order: str = "newest",
    ) -> dict[str, Any]:
        """
        返回错误日志分页数据；若版本未变则返回 data=null。

        :param known_rev: 客户端已知的版本号，默认 -1
        :param page: 页码，默认 1
        :param page_size: 每页大小，默认 10
        :param node: 节点名称过滤，默认 ""
        :param keyword: 关键词过滤，默认 ""
        :param sort_order: 排序方式，支持 newest / oldest
        :return: {"rev": int, "page": int, "page_size": int, "total": int, "total_pages": int, "data": list | None}
        """
        (
            normalized_page,
            normalized_page_size,
            normalized_node,
            normalized_keyword,
            normalized_sort_order,
        ) = normalize_errors_query(page, page_size, node, keyword, sort_order)
        rev, total, total_pages, page_items = server.get_errors_page(
            normalized_page,
            normalized_page_size,
            normalized_node,
            normalized_keyword,
            normalized_sort_order,
        )

        base = {
            "rev": rev,
            "page": min(normalized_page, total_pages),
            "page_size": normalized_page_size,
            "total": total,
            "total_pages": total_pages,
            "sort_order": normalized_sort_order,
        }
        if known_rev == rev:
            return {**base, "data": None}
        return {**base, "data": page_items}

    @router.get("/api/pull_analysis")
    def pull_analysis(known_rev: int = -1) -> dict[str, Any]:
        """
        返回图拓扑信息。

        :param known_rev: 客户端已知的版本号
        :return: {"rev": int, "data": dict | None}
        """
        rev, analysis_store = server.get_analysis_snapshot()
        return {"rev": rev, "data": analysis_store}

    @router.get("/api/pull_error_type_counts")
    def pull_error_type_counts(known_rev: int = -1, node: str = "") -> dict[str, Any]:
        """
        返回按错误类型聚合后的统计结果；若版本未变则返回 data=null。

        :param known_rev: 客户端已知的版本号，默认 -1
        :param node: 节点名称过滤，默认 ""
        :return: {"rev": int, "data": list[dict[str, Any]] | None}
        """
        rev, items = server.get_error_type_counts(node)
        if known_rev == rev:
            return {"rev": rev, "data": None}
        return {"rev": rev, "data": items}
