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

## 使用示例

### 格式化错误信息函数的用法示例

```python
from celestialflow.web.util_error import (
    normalize_errors_query,
    filter_errors,
    paginate_errors,
)

# 模拟一批错误记录
error_store = [
    {"ts": 1005, "error_id": "E001", "error_repr": "连接超时", "stage": "StageA", "task_repr": "task_1"},
    {"ts": 1003, "error_id": "E002", "error_repr": "内存不足", "stage": "StageB", "task_repr": "task_5"},
    {"ts": 1008, "error_id": "E003", "error_repr": "连接超时", "stage": "StageA", "task_repr": "task_2"},
    {"ts": 1001, "error_id": "E004", "error_repr": "文件未找到", "stage": "StageC", "task_repr": "task_3"},
    {"ts": 1010, "error_id": "E005", "error_repr": "权限不足", "stage": "StageB", "task_repr": "task_4"},
]

# 1. normalize_errors_query: 归一化查询参数
page, page_size, node, keyword = normalize_errors_query(
    page=0,           # 会被限制为 1
    page_size=50,      # 保持 50
    node=" StageA ",   # 空格被去除
    keyword=" 超时 ",  # 空格去除并转小写
)
print(f"归一化结果: page={page}, page_size={page_size}, node='{node}', keyword='{keyword}'")
# 输出: page=1, page_size=50, node='StageA', keyword='超时'

# 2. filter_errors: 按节点和关键词过滤
filtered = filter_errors(error_store, node, keyword)
print(f"\n过滤结果 ({len(filtered)} 条):")
for err in filtered:
    print(f"  [{err['error_id']}] {err['error_repr']} - {err['stage']}")
# 输出：
#   [E001] 连接超时 - StageA
#   [E003] 连接超时 - StageA

# 3. paginate_errors: 分页（每页 2 条）
total, total_pages, page_items = paginate_errors(filtered, 1, 2)
print(f"\n分页结果: 共 {total} 条, {total_pages} 页, 当前第 1 页 {len(page_items)} 条")
for err in page_items:
    print(f"  [{err['error_id']}] {err['error_repr']}")
# 输出：
#   共 2 条, 1 页, 当前第 1 页 2 条
#   [E003] 连接超时  (时间戳降序，1008 > 1005)
#   [E001] 连接超时

# 4. 完整查询链路：只查 StageB 且关键词包含不足
print("\n" + "=" * 40)
print("完整查询链路示例")
print("=" * 40)

page, page_size, node, keyword = normalize_errors_query(1, 10, "StageB", "不足")
filtered = filter_errors(error_store, node, keyword)
total, total_pages, items = paginate_errors(filtered, page, page_size)
print(f"查询结果: 共 {total} 条")
for item in items:
    print(f"  [{item['error_id']}] {item['error_repr']} @ {item['stage']}")
# 输出：
#   查询结果: 共 1 条
#   [E002] 内存不足 @ StageB
```
