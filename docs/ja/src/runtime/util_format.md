# src/celestialflow/runtime/util_format.py

> 📅 最終更新日: 2026/10/30

`runtime/util_format.py` は汎用フォーマットユーティリティ関数を提供し、文字列の切り詰め、テーブルレンダリング、値クラスタリングなどの機能を含みます。

## 主要関数

| 関数 | 説明 |
|------|------|
| `format_repr(obj, max_length)` | オブジェクトの文字列を安全に切り詰め、改行とバックスラッシュを自動的にエスケープ |
| `format_table(data, ...)` | 二次元データをテキストテーブルにレンダリング。`left` / `right` / `center` の配置をサポート |
| `cluster_by_value_sorted(input_dict)` | 値ごとにクラスタリングし、value の昇順でソート |

## format_repr

```python
def format_repr(obj: Any, max_length: int) -> str: ...
```

オブジェクトを文字列にフォーマットし、改行とバックスラッシュを自動的にエスケープします。長すぎる場合は `先頭 2/3 + ... + 末尾 1/3` の形で切り詰めます：

- まず `str(obj)` を実行し、次にバックスラッシュを二重化（`\` → `\\`）し、改行を 2 文字の `\` + `n` に置換します
- `max_length <= 0` または長さが上限を超えていない場合はそのまま返します（切り詰めなし）
- 切り詰める場合、`segment_len = max(1, max_length // 3)` とし、先頭 `2 * segment_len` 文字 + `...` + 末尾 `segment_len` 文字を取得します

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

- `data` が空の場合は文字列 `"表格数据为空！"` を返します
- `column_names` が省略された、または数が不足している場合は Excel 形式で自動的に名前を補います；`row_names` が省略された場合は `0..n-1` を行番号として使用します
- 行と列の長さが一致しない場合は `fill_value` で埋めます
- `align` は `"left"` / `"right"` / `"center"` をサポートし、未知の値は左揃えにフォールバックします

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
)

# format_repr: 安全な切り詰め
print(format_repr("hello world", 50))  # hello world
print(format_repr("A" * 100, 30))  # AAAAAAAAAAAAAAAAAAAA...AAAAAAAAAA（20 + 3 + 10）
print(format_repr("a\nb", 50))  # a\nb（改行はリテラル \n にエスケープされる）
print(format_repr("A" * 100, 0))  # 切り詰めなし。完全な 100 個の A を返す

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
