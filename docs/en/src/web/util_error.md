# util_error

> 📅 Last Updated: 2026/06/22

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

Error filtering and pagination are directly handled by SQLite's `query_records`; this module is only responsible for query parameter normalization.

## Usage Example

### normalize_errors_query Usage Example

```python
from celestialflow.web.util_error import normalize_errors_query

# Normalize query parameters
page, page_size, node, keyword, sort_order = normalize_errors_query(
    page=0,           # will be clamped to 1
    page_size=50,      # stays at 50
    node=" StageA ",   # whitespace stripped
    keyword=" timeout ",  # whitespace stripped and lowercased
    sort_order="newest",  # valid value, kept as is
)
print(f"Normalized results: page={page}, page_size={page_size}, node='{node}', keyword='{keyword}', sort_order='{sort_order}'")
# Output: page=1, page_size=50, node='StageA', keyword='timeout', sort_order='newest'

# Illegal sort_order value falls back to newest
_, _, _, _, sort_order = normalize_errors_query(1, 10, "", "", "invalid")
print(f"Illegal sort value normalized: {sort_order}")  # newest

# Typical error query parameters
page, page_size, node, keyword, sort_order = normalize_errors_query(1, 10, "StageB", "insufficient", "oldest")
print(f"Query StageB containing 'insufficient': page={page}, page_size={page_size}, node='{node}', keyword='{keyword}', sort_order='{sort_order}'")
```
