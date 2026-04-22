# util_error

Web 模块的错误查询与分页工具函数。

## normalize_errors_query

```python
def normalize_errors_query(
    page: int, page_size: int, node: str, keyword: str
) -> tuple[int, int, str, str]:
    """归一化错误查询参数。"""
```

将用户输入的查询参数进行归一化处理：限制 `page_size` 在 [1, 200]、`page` >= 1、去除空白、关键词转小写。

## filter_errors

```python
def filter_errors(
    error_store: list[dict[str, Any]], normalized_node: str, normalized_keyword: str
) -> list[dict[str, Any]]:
    """根据节点名和关键词过滤错误记录。"""
```

支持按 stage 名精确匹配和按 error_repr/task_repr 关键词模糊匹配。

## paginate_errors

```python
def paginate_errors(
    filtered: list[dict[str, Any]], normalized_page: int, normalized_page_size: int
) -> tuple[int, int, list[dict[str, Any]]]:
    """对过滤后的错误记录进行分页，返回 (总数, 总页数, 当前页记录)。"""
```

按时间戳降序排列后分页。
