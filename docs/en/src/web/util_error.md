# util_error

> 📅 Last Updated: 2026/05/23

Error query, filtering, and pagination utility functions for the Web module.

## normalize_errors_query

```python
def normalize_errors_query(
    page: int, page_size: int, node: str, keyword: str
) -> tuple[int, int, str, str]:
    """Normalize error query parameters."""
```

- Clamps `page_size` to the [1, 200] range.
- Clamps `page` to a minimum of 1.
- Strips leading and trailing whitespace from node name and keyword, and converts keyword to lowercase.

## filter_errors

```python
def filter_errors(
    error_store: list[dict[str, Any]], normalized_node: str, normalized_keyword: str
) -> list[dict[str, Any]]:
    """Filter error records by node name and keyword."""
```

- **Node Filtering**: If `normalized_node` is non-empty, only errors from that node are retained.
- **Keyword Search**: If `normalized_keyword` is non-empty, performs fuzzy matching in `error_repr` (error representation) and `task_repr` (task representation).

## paginate_errors

```python
def paginate_errors(
    filtered: list[dict[str, Any]], normalized_page: int, normalized_page_size: int
) -> tuple[int, int, list[dict[str, Any]]]:
    """Paginate filtered error records, returning (total count, total pages, current page records)."""
```

- Sorts by timestamp in descending order (newest errors first).
- Accurately calculates total record count and total page count.

## Usage Examples

### Usage Examples for Error Formatting Functions

```python
from celestialflow.web.util_error import (
    normalize_errors_query,
    filter_errors,
    paginate_errors,
)

# Simulate a batch of error records
error_store = [
    {"ts": 1005, "error_id": "E001", "error_repr": "连接超时", "stage": "StageA", "task_repr": "task_1"},
    {"ts": 1003, "error_id": "E002", "error_repr": "内存不足", "stage": "StageB", "task_repr": "task_5"},
    {"ts": 1008, "error_id": "E003", "error_repr": "连接超时", "stage": "StageA", "task_repr": "task_2"},
    {"ts": 1001, "error_id": "E004", "error_repr": "文件未找到", "stage": "StageC", "task_repr": "task_3"},
    {"ts": 1010, "error_id": "E005", "error_repr": "权限不足", "stage": "StageB", "task_repr": "task_4"},
]

# 1. normalize_errors_query: Normalize query parameters
page, page_size, node, keyword = normalize_errors_query(
    page=0,           # Will be clamped to 1
    page_size=50,      # Kept as 50
    node=" StageA ",   # Whitespace stripped
    keyword=" 超时 ",  # Whitespace stripped and lowercased
)
print(f"归一化结果: page={page}, page_size={page_size}, node='{node}', keyword='{keyword}'")
# Output: page=1, page_size=50, node='StageA', keyword='超时'

# 2. filter_errors: Filter by node and keyword
filtered = filter_errors(error_store, node, keyword)
print(f"\n过滤结果 ({len(filtered)} 条):")
for err in filtered:
    print(f"  [{err['error_id']}] {err['error_repr']} - {err['stage']}")
# Output:
#   [E001] 连接超时 - StageA
#   [E003] 连接超时 - StageA

# 3. paginate_errors: Paginate (2 items per page)
total, total_pages, page_items = paginate_errors(filtered, 1, 2)
print(f"\n分页结果: 共 {total} 条, {total_pages} 页, 当前第 1 页 {len(page_items)} 条")
for err in page_items:
    print(f"  [{err['error_id']}] {err['error_repr']}")
# Output:
#   共 2 条, 1 页, 当前第 1 页 2 条
#   [E003] 连接超时  (descending by timestamp, 1008 > 1005)
#   [E001] 连接超时

# 4. Complete query pipeline: only query StageB with keyword containing 不足
print("\n" + "=" * 40)
print("完整查询链路示例")
print("=" * 40)

page, page_size, node, keyword = normalize_errors_query(1, 10, "StageB", "不足")
filtered = filter_errors(error_store, node, keyword)
total, total_pages, items = paginate_errors(filtered, page, page_size)
print(f"查询结果: 共 {total} 条")
for item in items:
    print(f"  [{item['error_id']}] {item['error_repr']} @ {item['stage']}")
# Output:
#   查询结果: 共 1 条
#   [E002] 内存不足 @ StageB
```
