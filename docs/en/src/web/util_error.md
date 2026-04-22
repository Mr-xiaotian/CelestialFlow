# util_error

Error query and pagination utility functions for the Web module.

## normalize_errors_query

```python
def normalize_errors_query(
    page: int, page_size: int, node: str, keyword: str
) -> tuple[int, int, str, str]:
    """Normalize error query parameters."""
```

Normalizes user-input query parameters: clamps `page_size` to [1, 200], ensures `page` >= 1, strips whitespace, and converts keywords to lowercase.

## filter_errors

```python
def filter_errors(
    error_store: list[dict[str, Any]], normalized_node: str, normalized_keyword: str
) -> list[dict[str, Any]]:
    """Filter error records by stage name and keyword."""
```

Supports exact matching by stage name and fuzzy matching by error_repr/task_repr keyword.

## paginate_errors

```python
def paginate_errors(
    filtered: list[dict[str, Any]], normalized_page: int, normalized_page_size: int
) -> tuple[int, int, list[dict[str, Any]]]:
    """Paginate filtered error records, returning (total count, total pages, current page records)."""
```

Sorts by timestamp in descending order before paginating.
