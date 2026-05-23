# util_error

> 📅 最后更新日期: 2026/05/23

Web 模块的错误查询、过滤与分页工具函数。

## normalize_errors_query

```python
def normalize_errors_query(
    page: int, page_size: int, node: str, keyword: str
) -> tuple[int, int, str, str]:
    """归一化错误查询参数。"""
```

- 限制 `page_size` 在 [1, 200] 之间。
- 限制 `page` 最小为 1。
- 去除节点名与关键词的首尾空格，并将关键词转为小写。

## filter_errors

```python
def filter_errors(
    error_store: list[dict[str, Any]], normalized_node: str, normalized_keyword: str
) -> list[dict[str, Any]]:
    """根据节点名和关键词过滤错误记录。"""
```

- **节点过滤**: 若 `normalized_node` 非空，则仅保留该节点的错误。
- **关键词搜索**: 若 `normalized_keyword` 非空，则在 `error_repr` (错误表示) 和 `task_repr` (任务表示) 中进行模糊匹配。

## paginate_errors

```python
def paginate_errors(
    filtered: list[dict[str, Any]], normalized_page: int, normalized_page_size: int
) -> tuple[int, int, list[dict[str, Any]]]:
    """对过滤后的错误记录进行分页，返回 (总数, 总页数, 当前页记录)。"""
```

- 按时间戳降序排列（最新错误在前）。
- 准确计算总记录数和总页数。
