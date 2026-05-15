# util_error

> 📅 最終更新日: 2026/04/22

Web モジュールのエラークエリおよびページネーションユーティリティ関数。

## normalize_errors_query

```python
def normalize_errors_query(
    page: int, page_size: int, node: str, keyword: str
) -> tuple[int, int, str, str]:
    """エラークエリパラメータを正規化する。"""
```

ユーザー入力のクエリパラメータを正規化します：`page_size` を [1, 200] に制限、`page` >= 1 を保証、空白を除去、キーワードを小文字に変換。

## filter_errors

```python
def filter_errors(
    error_store: list[dict[str, Any]], normalized_node: str, normalized_keyword: str
) -> list[dict[str, Any]]:
    """ノード名とキーワードでエラーレコードをフィルタリングする。"""
```

ステージ名による完全一致と error_repr/task_repr キーワードによるあいまい一致をサポートします。

## paginate_errors

```python
def paginate_errors(
    filtered: list[dict[str, Any]], normalized_page: int, normalized_page_size: int
) -> tuple[int, int, list[dict[str, Any]]]:
    """フィルタリング済みエラーレコードをページネーションし、(総数, 総ページ数, 現在ページのレコード) を返す。"""
```

ページネーション前にタイムスタンプの降順でソートします。
