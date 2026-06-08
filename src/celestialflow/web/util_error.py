# web/util_error.py
from typing import Any


def normalize_errors_query(
    page: int, page_size: int, node: str, keyword: str, sort_order: str
) -> tuple[int, int, str, str, str]:
    """
    归一化错误查询参数，返回归一化后的页面、每页大小、节点和关键词。

    :param page: 页码
    :param page_size: 每页大小
    :param node: 节点名称
    :param keyword: 搜索关键词
    :param sort_order: 排序方式
    :return: (归一化页码, 归一化每页大小, 归一化节点名, 归一化关键词, 排序方式)
    """
    normalized_page_size = max(1, min(int(page_size), 200))
    normalized_page = max(1, int(page))
    normalized_node = node.strip()
    normalized_keyword = keyword.strip().lower()
    normalized_sort_order = sort_order.strip().lower()
    if normalized_sort_order not in {"newest", "oldest"}:
        normalized_sort_order = "newest"
    return (
        normalized_page,
        normalized_page_size,
        normalized_node,
        normalized_keyword,
        normalized_sort_order,
    )


def filter_errors(
    error_store: list[dict[str, Any]], normalized_node: str, normalized_keyword: str
) -> list[dict[str, Any]]:
    """
    根据错误查询参数过滤错误记录，返回符合条件的记录。

    :param error_store: 错误记录列表
    :param normalized_node: 归一化后的节点名称
    :param normalized_keyword: 归一化后的搜索关键词
    :return: 符合条件的错误记录列表
    """
    filtered: list[dict[str, Any]] = []
    for item in error_store:
        stage = str(item.get("stage", ""))
        if normalized_node and stage != normalized_node:
            continue
        if normalized_keyword:
            error_type = str(item.get("error_type", "")).lower()
            error_message = str(item.get("error_message", "")).lower()
            task = str(item.get("task", "")).lower()
            if (
                normalized_keyword not in error_type
                and normalized_keyword not in error_message
                and normalized_keyword not in task
            ):
                continue
        filtered.append(item)
    return filtered


def paginate_errors(
    filtered: list[dict[str, Any]],
    normalized_page: int,
    normalized_page_size: int,
    sort_order: str,
) -> tuple[int, int, list[dict[str, Any]]]:
    """
    根据归一化后的页面和每页大小，对错误记录进行分页处理，返回总记录数、总页数和当前页记录。

    :param filtered: 过滤后的错误记录列表
    :param normalized_page: 归一化后的页码
    :param normalized_page_size: 归一化后的每页大小
    :param sort_order: 排序方式，支持 newest / oldest
    :return: (总记录数, 总页数, 当前页记录列表)
    """
    total = len(filtered)
    total_pages = max(1, (total + normalized_page_size - 1) // normalized_page_size)
    normalized_page = min(normalized_page, total_pages)
    reverse = sort_order != "oldest"
    sorted_items = sorted(filtered, key=lambda item: item.get("ts", 0), reverse=reverse)
    start_index = (normalized_page - 1) * normalized_page_size
    end_index = start_index + normalized_page_size
    return total, total_pages, sorted_items[start_index:end_index]
