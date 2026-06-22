# util_error

> 📅 最終更新日: 2026/06/22

Web モジュールのエラークエリ、フィルタリング、ページングユーティリティ関数。

## normalize_errors_query

```python
def normalize_errors_query(
    page: int, page_size: int, node: str, keyword: str, sort_order: str
) -> tuple[int, int, str, str, str]:
    """エラークエリパラメータを正規化します（ソート方式を含む）。"""
```

- `page_size` を [1, 200] の範囲に制限します。
- `page` を最小 1 に制限します。
- ノード名とキーワードの前後空白を除去し、キーワードを小文字に変換します。
- `sort_order` を `"newest"` または `"oldest"` に正規化し、無効な値はデフォルトで `"newest"` になります。

エラーのフィルタリングとページングは SQLite レイヤーの `query_records` で直接処理され、本モジュールはクエリパラメータの正規化のみを担当します。

## 使用例

### normalize_errors_query の使用例

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
print(f"正規化結果: page={page}, page_size={page_size}, node='{node}', keyword='{keyword}', sort_order='{sort_order}'")
# 输出: page=1, page_size=50, node='StageA', keyword='超时', sort_order='newest'

# sort_order 非法值回退为 newest
_, _, _, _, sort_order = normalize_errors_query(1, 10, "", "", "invalid")
print(f"無効なソート値の正規化: {sort_order}")  # newest

# 典型错误查询参数
page, page_size, node, keyword, sort_order = normalize_errors_query(1, 10, "StageB", "不足", "oldest")
print(f"StageB に '不足' を含むクエリ: page={page}, page_size={page_size}, node='{node}', keyword='{keyword}', sort_order='{sort_order}'")
```
