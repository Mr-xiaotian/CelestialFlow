# RuntimeFormat

> 📅 最終更新日: 2026/08/12

`runtime/util_format.py` は汎用フォーマットユーティリティ関数を提供し、文字列の切り詰め、テーブルレンダリング、時間フォーマットなどの機能を含みます。

> 注意: 現在のファイルパスは `src/celestialflow/runtime/util_format.py` です。旧パス `src/celestialflow/utils/util_format.py` は廃止されました。

## 主要関数

| 関数 | 説明 |
|------|------|
| `format_repr(obj, max_length)` | オブジェクトの文字列を安全に切り詰め、改行とバックスラッシュを自動的にエスケープ |
| `format_table(data, ...)` | 二次元データをテキストテーブルにレンダリング。`left` / `right` / `center` の配置をサポート |
| `format_duration(seconds)` | 秒数を可読な時間形式（`MM:SS` または `HH:MM:SS`）に変換 |
| `format_timestamp(timestamp)` | タイムスタンプを `YYYY-MM-DD HH:MM:SS` 形式の文字列に変換 |
| `cluster_by_value_sorted(input_dict)` | 値ごとにクラスタリングし、value の昇順でソート |

## format_repr

```python
def format_repr(obj: Any, max_length: int) -> str: ...
```

オブジェクトを文字列にフォーマットし、改行とバックスラッシュを自動的にエスケープします。長すぎる場合は `先頭 2/3 + ... + 末尾 1/3` の形で切り詰めます。

## format_table

```python
def format_table(
    data: list[Any],
    row_names: list[Any] | None = None,
    column_names: list[str] | None = None,
    index_header: str = "#",
    fill_value: str = "N/A",
    align: str = "left",
) -> str: ...
```

二次元データをボーダー付きテキストテーブルにフォーマットします。Excel 形式の列名（A, B, ..., Z, AA, AB...）の自動生成に対応します。

## format_duration

```python
def format_duration(seconds: int) -> str: ...
```

秒数を `HH:MM:SS` または `MM:SS` 形式にフォーマットします。時が 0 の場合は先頭のゼロを自動的に省略します。

## format_timestamp

```python
def format_timestamp(timestamp: float) -> str: ...
```

タイムスタンプ（秒）を `YYYY-MM-DD HH:MM:SS` 形式にフォーマットします。

## cluster_by_value_sorted

```python
def cluster_by_value_sorted(input_dict: dict[str, int]) -> dict[int, list[str]]: ...
```

値ごとにクラスタリングし、結果を value（整数キー）の昇順でソートします。`TaskGraph._build_analysis()` で階層辞書を構築するために使用されます。

## 使用例

```python
from celestialflow.runtime.util_format import (
    format_repr,
    format_table,
    format_duration,
    format_timestamp,
)

# format_repr: 安全な切り詰め
print(format_repr("hello world", 50))  # hello world
print(format_repr("A" * 100, 30))  # AAAAAAAAAAAAAAAAAAAA...CCCCCCCCCC

# format_duration: 時間フォーマット
print(format_duration(59))  # 00:59
print(format_duration(3661))  # 01:01:01

# format_timestamp: タイムスタンプフォーマット
print(format_timestamp(0))  # 1970-01-01 08:00:00

# format_table: テーブルレンダリング
data = [
    ["serial", 100, 2.34],
    ["thread", 100, 0.89],
]
table = format_table(
    data=data,
    column_names=["モード", "タスク数", "時間(s)"],
)
print(table)
```

## cluster_by_value_sorted の例

```python
from celestialflow.runtime.util_format import cluster_by_value_sorted

input_dict = {"A": 2, "B": 0, "C": 2, "D": 1}
result = cluster_by_value_sorted(input_dict)
print(result)  # {0: ['B'], 1: ['D'], 2: ['A', 'C']}
```
