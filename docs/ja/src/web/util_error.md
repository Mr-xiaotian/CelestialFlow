# util_error

> 📅 最終更新日: 2026/06/11

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

## filter_errors

```python
def filter_errors(
    error_store: list[dict[str, Any]], normalized_node: str, normalized_keyword: str
) -> list[dict[str, Any]]:
    """ノード名とキーワードに基づいてエラー記録をフィルタリングします。"""
```

- **ノードフィルタ**: `normalized_node` が空でない場合、そのノード（フィールド `stage` にマッチ）のエラーのみを保持します。
- **キーワード検索**: `normalized_keyword` が空でない場合、`error_type`（エラータイプ）、`error_message`（エラーメッセージ）、`task`（タスク）でファジーマッチを行います。

## paginate_errors

```python
def paginate_errors(
    filtered: list[dict[str, Any]],
    normalized_page: int,
    normalized_page_size: int,
    sort_order: str,
) -> tuple[int, int, list[dict[str, Any]]]:
    """フィルタリング後のエラー記録をページングし、(総数, 総ページ数, 現在ページの記録) を返します。"""
```

- `sort_order` に基づいてソートします（`"newest"` はタイムスタンプ降順、`"oldest"` は昇順）。
- 総記録数と総ページ数を正確に計算し、ページ番号が総ページ数を超えないようにクランプします。

## 使用例

### エラー情報フォーマット関数の使用例

```python
from celestialflow.web.util_error import (
    normalize_errors_query,
    filter_errors,
    paginate_errors,
)

# エラー記録のサンプルデータを生成
error_store = [
    {"ts": 1005, "error_id": "E001", "error_type": "接続タイムアウト", "error_message": "timeout", "stage": "StageA", "task": "task_1"},
    {"ts": 1003, "error_id": "E002", "error_type": "メモリ不足", "error_message": "oom", "stage": "StageB", "task": "task_5"},
    {"ts": 1008, "error_id": "E003", "error_type": "接続タイムアウト", "error_message": "timeout", "stage": "StageA", "task": "task_2"},
    {"ts": 1001, "error_id": "E004", "error_type": "ファイル未検出", "error_message": "not found", "stage": "StageC", "task": "task_3"},
    {"ts": 1010, "error_id": "E005", "error_type": "権限不足", "error_message": "access denied", "stage": "StageB", "task": "task_4"},
]

# 1. normalize_errors_query: クエリパラメータの正規化
page, page_size, node, keyword, sort_order = normalize_errors_query(
    page=0,           # 1に制限される
    page_size=50,      # 50のまま
    node=" StageA ",   # 空白が除去される
    keyword=" タイムアウト ",  # 空白除去・小文字化
    sort_order="newest",  # 有効値、そのまま維持
)
print(f"正規化結果: page={page}, page_size={page_size}, node='{node}', keyword='{keyword}', sort_order='{sort_order}'")
# 出力: page=1, page_size=50, node='StageA', keyword='タイムアウト', sort_order='newest'

# 2. filter_errors: ノードとキーワードでフィルタ
filtered = filter_errors(error_store, node, keyword)
print(f"\nフィルタ結果 ({len(filtered)} 件):")
for err in filtered:
    print(f"  [{err['error_id']}] {err['error_type']} - {err['stage']}")
# 出力：
#   [E001] 接続タイムアウト - StageA
#   [E003] 接続タイムアウト - StageA

# 3. paginate_errors: ページング（1ページ2件、newest ソート）
total, total_pages, page_items = paginate_errors(filtered, 1, 2, "newest")
print(f"\nページング結果: 全 {total} 件, {total_pages} ページ, 現在1ページ目 {len(page_items)} 件")
for err in page_items:
    print(f"  [{err['error_id']}] {err['error_type']}")
# 出力：
#   全 2 件, 1 ページ, 現在1ページ目 2 件
#   [E003] 接続タイムアウト  (タイムスタンプ降順、1008 > 1005)
#   [E001] 接続タイムアウト

# 4. 完全なクエリチェーン：StageB のみ検索し、キーワードに不足を含む
print("\n" + "=" * 40)
print("完全なクエリチェーン例")
print("=" * 40)

page, page_size, node, keyword, sort_order = normalize_errors_query(1, 10, "StageB", "不足", "newest")
filtered = filter_errors(error_store, node, keyword)
total, total_pages, items = paginate_errors(filtered, page, page_size, sort_order)
print(f"クエリ結果: 全 {total} 件")
for item in items:
    print(f"  [{item['error_id']}] {item['error_type']} @ {item['stage']}")
# 出力：
#   クエリ結果: 全 1 件
#   [E002] メモリ不足 @ StageB
```
