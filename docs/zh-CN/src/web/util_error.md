# util_error

> 📅 最后更新日期: 2026/06/22

Web 模块的错误查询、过滤与分页工具函数。

## normalize_errors_query

```python
def normalize_errors_query(
    page: int, page_size: int, node: str, keyword: str, sort_order: str
) -> tuple[int, int, str, str, str]:
    """归一化错误查询参数（含排序方式）。"""
```

- 限制 `page_size` 在 [1, 200] 之间。
- 限制 `page` 最小为 1。
- 去除节点名与关键词的首尾空格，并将关键词转为小写。
- `sort_order` 归一化为 `"newest"` 或 `"oldest"`，非法值默认 `"newest"`。

错误过滤与分页由 SQLite 层面的 `query_records` 直接处理，本模块仅负责查询参数归一化。

## 使用示例

### normalize_errors_query 用法示例

```python
from celestialflow.web.util_error import normalize_errors_query

# 归一化查询参数
page, page_size, node, keyword, sort_order = normalize_errors_query(
    page=0,           # 会被限制为 1
    page_size=50,      # 保持 50
    node=" StageA ",   # 空格被去除
    keyword=" 超时 ",  # 空格去除并转小写
    sort_order="newest",  # 有效值，保持不变
)
print(f"归一化结果: page={page}, page_size={page_size}, node='{node}', keyword='{keyword}', sort_order='{sort_order}'")
# 输出: page=1, page_size=50, node='StageA', keyword='超时', sort_order='newest'

# sort_order 非法值回退为 newest
_, _, _, _, sort_order = normalize_errors_query(1, 10, "", "", "invalid")
print(f"非法排序值归一化: {sort_order}")  # newest

# 典型错误查询参数
page, page_size, node, keyword, sort_order = normalize_errors_query(1, 10, "StageB", "不足", "oldest")
print(f"查询 StageB 含'不足': page={page}, page_size={page_size}, node='{node}', keyword='{keyword}', sort_order='{sort_order}'")
```
