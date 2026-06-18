# util_error

> 📅 Last Updated: 2026/06/18

Web module error querying, filtering, and pagination utility functions.

## normalize_errors_query

```python
def normalize_errors_query(
    page: int, page_size: int, node: str, keyword: str, sort_order: str
) -> tuple[int, int, str, str, str]:
    """Normalizes error query parameters (including sort order)."""
```

- Clamps `page_size` within [1, 200].
- Clamps `page` to a minimum of 1.
- Strips leading/trailing whitespace from node name and keyword, and lowercases the keyword.
- Normalizes `sort_order` to `"newest"` or `"oldest"`; illegal values default to `"newest"`.

## filter_errors

```python
def filter_errors(
    error_store: list[dict[str, Any]], normalized_node: str, normalized_keyword: str
) -> list[dict[str, Any]]:
    """Filters error records by node name and keyword."""
```

- **Node filtering**: If `normalized_node` is non-empty, only retains errors for that node (matching field `stage`).
- **Keyword search**: If `normalized_keyword` is non-empty, performs fuzzy matching across `error_type`, `error_message`, and `task`.

## paginate_errors

```python
def paginate_errors(
    filtered: list[dict[str, Any]],
    normalized_page: int,
    normalized_page_size: int,
    sort_order: str,
) -> tuple[int, int, list[dict[str, Any]]]:
    """Paginates filtered error records, returning (total_count, total_pages, current_page_records)."""
```

- Sorts by `sort_order` (`"newest"` = timestamp descending, `"oldest"` = ascending).
- Accurately calculates total records and total pages, clamping the page number to not exceed total pages.

## Usage Examples

### Usage Examples for Error Formatting Functions

```python
from celestialflow.web.util_error import (
    normalize_errors_query,
    filter_errors,
    paginate_errors,
)

# Simulated batch of error records
error_store = [
    {"ts": 1005, "error_id": "E001", "error_type": "Connection Timeout", "error_message": "timeout", "stage": "StageA", "task": "task_1"},
    {"ts": 1003, "error_id": "E002", "error_type": "Out of Memory", "error_message": "oom", "stage": "StageB", "task": "task_5"},
    {"ts": 1008, "error_id": "E003", "error_type": "Connection Timeout", "error_message": "timeout", "stage": "StageA", "task": "task_2"},
    {"ts": 1001, "error_id": "E004", "error_type": "File Not Found", "error_message": "not found", "stage": "StageC", "task": "task_3"},
    {"ts": 1010, "error_id": "E005", "error_type": "Permission Denied", "error_message": "access denied", "stage": "StageB", "task": "task_4"},
]

# 1. normalize_errors_query: Normalize query parameters
page, page_size, node, keyword, sort_order = normalize_errors_query(
    page=0,           # will be clamped to 1
    page_size=50,      # stays at 50
    node=" StageA ",   # whitespace stripped
    keyword=" timeout ",  # whitespace stripped and lowercased
    sort_order="newest",  # valid value, kept as is
)
print(f"Normalized results: page={page}, page_size={page_size}, node='{node}', keyword='{keyword}', sort_order='{sort_order}'")
# Output: page=1, page_size=50, node='StageA', keyword='timeout', sort_order='newest'

# 2. filter_errors: Filter by node and keyword
filtered = filter_errors(error_store, node, keyword)
print(f"\nFilter results ({len(filtered)} records):")
for err in filtered:
    print(f"  [{err['error_id']}] {err['error_type']} - {err['stage']}")
# Output:
#   [E001] Connection Timeout - StageA
#   [E003] Connection Timeout - StageA

# 3. paginate_errors: Paginate (2 per page, sorted by newest)
total, total_pages, page_items = paginate_errors(filtered, 1, 2, "newest")
print(f"\nPagination result: total {total}, {total_pages} pages, current page 1 has {len(page_items)} records")
for err in page_items:
    print(f"  [{err['error_id']}] {err['error_type']}")
# Output:
#   total 2, 1 pages, current page 1 has 2 records
#   [E003] Connection Timeout  (timestamp descending, 1008 > 1005)
#   [E001] Connection Timeout

# 4. Full query pipeline: only StageB with keyword containing "memory"
print("\n" + "=" * 40)
print("Full query pipeline example")
print("=" * 40)

page, page_size, node, keyword, sort_order = normalize_errors_query(1, 10, "StageB", "memory", "newest")
filtered = filter_errors(error_store, node, keyword)
total, total_pages, items = paginate_errors(filtered, page, page_size, sort_order)
print(f"Query result: total {total} records")
for item in items:
    print(f"  [{item['error_id']}] {item['error_type']} @ {item['stage']}")
# Output:
#   Query result: total 1 record
#   [E002] Out of Memory @ StageB
```
