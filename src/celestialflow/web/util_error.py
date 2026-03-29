# web/util_error.py
from typing import Any


def normalize_errors_query(
    page: int, page_size: int, node: str, keyword: str
) -> tuple[int, int, str, str]:
    """
    归一化错误查询参数，返回归一化后的页面、每页大小、节点和关键词。
    """
    normalized_page_size = max(1, min(int(page_size), 200))
    normalized_page = max(1, int(page))
    normalized_node = node.strip()
    normalized_keyword = keyword.strip().lower()
    return normalized_page, normalized_page_size, normalized_node, normalized_keyword


def filter_errors(
    error_store: list[dict[str, Any]], normalized_node: str, normalized_keyword: str
) -> list[dict[str, Any]]:
    """
    根据错误查询参数过滤错误记录，返回符合条件的记录。
    """
    filtered: list[dict[str, Any]] = []
    for item in error_store:
        stage = str(item.get("stage", ""))
        if normalized_node and stage != normalized_node:
            continue
        if normalized_keyword:
            error_repr = str(item.get("error_repr", "")).lower()
            task_repr = str(item.get("task_repr", "")).lower()
            if (
                normalized_keyword not in error_repr
                and normalized_keyword not in task_repr
            ):
                continue
        filtered.append(item)
    return filtered


def paginate_errors(
    filtered: list[dict[str, Any]], normalized_page: int, normalized_page_size: int
) -> tuple[int, int, list[dict[str, Any]]]:
    """
    根据归一化后的页面和每页大小，对错误记录进行分页处理，返回总记录数、总页数和当前页记录。
    """
    total = len(filtered)
    total_pages = max(1, (total + normalized_page_size - 1) // normalized_page_size)
    normalized_page = min(normalized_page, total_pages)
    sorted_items = sorted(filtered, key=lambda item: item.get("ts", 0), reverse=True)
    start_index = (normalized_page - 1) * normalized_page_size
    end_index = start_index + normalized_page_size
    return total, total_pages, sorted_items[start_index:end_index]
