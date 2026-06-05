# util_error

> 📅 最終更新日: 2026/05/23

Web モジュールのエラークエリ、フィルタリング、ページネーションのユーティリティ関数です。

## normalize_errors_query

```python
def normalize_errors_query(
    page: int, page_size: int, node: str, keyword: str
) -> tuple[int, int, str, str]:
    """エラークエリパラメータを正規化します。"""
```

- `page_size` を [1, 200] の範囲に制限します。
- `page` の最小値を 1 に制限します。
- ノード名とキーワードの前後の空白を除去し、キーワードを小文字に変換します。

## filter_errors

```python
def filter_errors(
    error_store: list[dict[str, Any]], normalized_node: str, normalized_keyword: str
) -> list[dict[str, Any]]:
    """ノード名とキーワードでエラーレコードをフィルタリングします。"""
```

- **ノードフィルタリング**: `normalized_node` が空でない場合、そのノードのエラーのみを保持します。
- **キーワード検索**: `normalized_keyword` が空でない場合、`error_repr`（エラー表現）および `task_repr`（タスク表現）内であいまい一致を行います。

## paginate_errors

```python
def paginate_errors(
    filtered: list[dict[str, Any]], normalized_page: int, normalized_page_size: int
) -> tuple[int, int, list[dict[str, Any]]]:
    """フィルタリング済みエラーレコードをページネーションし、(総数, 総ページ数, 現在ページのレコード) を返します。"""
```

- タイムスタンプの降順でソートします（最新のエラーが先頭）。
- 総レコード数と総ページ数を正確に計算します。

## 使用例

### エラー情報フォーマット関数の使用例

```python
from celestialflow.web.util_error import (
    normalize_errors_query,
    filter_errors,
    paginate_errors,
)

# エラーレコードのサンプルデータ
error_store = [
    {"ts": 1005, "error_id": "E001", "error_repr": "接続タイムアウト", "stage": "StageA", "task_repr": "task_1"},
    {"ts": 1003, "error_id": "E002", "error_repr": "メモリ不足", "stage": "StageB", "task_repr": "task_5"},
    {"ts": 1008, "error_id": "E003", "error_repr": "接続タイムアウト", "stage": "StageA", "task_repr": "task_2"},
    {"ts": 1001, "error_id": "E004", "error_repr": "ファイルが見つかりません", "stage": "StageC", "task_repr": "task_3"},
    {"ts": 1010, "error_id": "E005", "error_repr": "権限不足", "stage": "StageB", "task_repr": "task_4"},
]

# 1. normalize_errors_query: クエリパラメータの正規化
page, page_size, node, keyword = normalize_errors_query(
    page=0,           # 1 に制限されます
    page_size=50,      # 50 のまま維持
    node=" StageA ",   # 空白が除去されます
    keyword=" タイムアウト ",  # 空白が除去され小文字に変換されます
)
print(f"正規化結果: page={page}, page_size={page_size}, node='{node}', keyword='{keyword}'")
# 出力: page=1, page_size=50, node='StageA', keyword='タイムアウト'

# 2. filter_errors: ノードとキーワードでフィルタリング
filtered = filter_errors(error_store, node, keyword)
print(f"\nフィルタリング結果 ({len(filtered)} 件):")
for err in filtered:
    print(f"  [{err['error_id']}] {err['error_repr']} - {err['stage']}")
# 出力：
#   [E001] 接続タイムアウト - StageA
#   [E003] 接続タイムアウト - StageA

# 3. paginate_errors: ページネーション（1ページ 2 件）
total, total_pages, page_items = paginate_errors(filtered, 1, 2)
print(f"\nページネーション結果: 全 {total} 件, {total_pages} ページ, 現在 1 ページ目 {len(page_items)} 件")
for err in page_items:
    print(f"  [{err['error_id']}] {err['error_repr']}")
# 出力：
#   全 2 件, 1 ページ, 現在 1 ページ目 2 件
#   [E003] 接続タイムアウト  (タイムスタンプ降順、1008 > 1005)
#   [E001] 接続タイムアウト

# 4. 完全なクエリチェーン：StageB のみ、かつキーワードに「不足」を含む
print("\n" + "=" * 40)
print("完全なクエリチェーンの例")
print("=" * 40)

page, page_size, node, keyword = normalize_errors_query(1, 10, "StageB", "不足")
filtered = filter_errors(error_store, node, keyword)
total, total_pages, items = paginate_errors(filtered, page, page_size)
print(f"クエリ結果: 全 {total} 件")
for item in items:
    print(f"  [{item['error_id']}] {item['error_repr']} @ {item['stage']}")
# 出力：
#   クエリ結果: 全 1 件
#   [E002] メモリ不足 @ StageB
```
