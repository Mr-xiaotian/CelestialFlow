# util_error

Web モジュールのエラークエリおよびページネーションユーティリティ関数です。

## normalize_errors_query

```python
def normalize_errors_query(
    page: int, page_size: int, node: str, keyword: str
) -> tuple[int, int, str, str]:
    """エラークエリパラメータを正規化します。"""
```

ユーザー入力のクエリパラメータを正規化します: `page_size` を [1, 200] に制限、`page` >= 1 を保証、空白を除去、キーワードを小文字に変換します。

## filter_errors

```python
def filter_errors(
    error_store: list[dict[str, Any]], normalized_node: str, normalized_keyword: str
) -> list[dict[str, Any]]:
    """ステージ名とキーワードでエラーレコードをフィルタリングします。"""
```

ステージ名による完全一致と error_repr/task_repr キーワードによるあいまい一致をサポートします。

## paginate_errors

```python
def paginate_errors(
    filtered: list[dict[str, Any]], normalized_page: int, normalized_page_size: int
) -> tuple[int, int, list[dict[str, Any]]]:
    """フィルタリングされたエラーレコードをページネーションし、（総数, 総ページ数, 現在のページのレコード）を返します。"""
```

タイムスタンプの降順でソートしてからページネーションします。
