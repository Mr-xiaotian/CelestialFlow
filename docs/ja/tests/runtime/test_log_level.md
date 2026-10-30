# tests/runtime/test_log_level.py

> 📅 最終更新日: 2026/10/30

## 役割
`celestialflow.runtime.util_log_level.normalize_log_level` の入力正規化とエラー分岐を検証します。レベル名は大文字小文字を区別せず、先頭・末尾の空白を無視します。また、未知のレベルと非文字列の入力はそれぞれ `InvalidOptionError` と `ConfigurationError` を送出します。

## コアテスト対象
- `normalize_log_level(log_level)`: ログレベルを検証・正規化し、`LEVEL_DICT` 内の大文字キー名を返します。非文字列なら `ConfigurationError`、許可集合に含まれなければ `InvalidOptionError` を送出します。
- `DEFAULT_LOG_LEVEL`: 実行エントリでログレベルを明示的に指定しない場合に使用されるデフォルト値（`"INFO"`）。同じモジュールで定義され、`run` / `restore_db` などのエントリのパラメータ既定値として使われます。
- `InvalidOptionError`: `ConfigurationError` を継承し、`field` / `value` / `allowed` を保持します。許可集合は `LEVEL_DICT` のキー（`TRACE`、`DEBUG`、`SUCCESS`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`）に由来します。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|--------|--------|---------|
| `TestNormalizeLogLevel` | 3 | 大文字小文字と空白の正規化、未知レベルの拒否、非文字列の拒否 |

## 主要テストシナリオ

### `TestNormalizeLogLevel`
1. **正規化** (`test_uppercases_and_strips`): `normalize_log_level(" error ")` は `"ERROR"` を返し、`strip().upper()` が効いていることを示します。
2. **未知レベルの拒否** (`test_rejects_unknown_level`): `normalize_log_level("VERBOSE")` は `InvalidOptionError` を送出します。
3. **非文字列の拒否** (`test_rejects_non_string`): `normalize_log_level(30)` は `ConfigurationError` を送出します（型チェックが値チェックより先に行われます）。

## テストの重点
- **入力の寛容さ**: 大文字小文字や先頭・末尾の空白は、正当なレベルの解釈に影響しません。
- **エラーの階層化**: 型エラーは `ConfigurationError`、値エラーはより具体的な `InvalidOptionError` を経由するため、呼び出し側は粒度に応じて捕捉できます。
- **許可集合の単一の情報源**: 正当なレベルは `LEVEL_DICT` のキーで決まり、テストと実装がそれぞれリストを保守する事態を避けます。

## 使用例

```python
from celestialflow.runtime.util_errors import ConfigurationError, InvalidOptionError
from celestialflow.runtime.util_log_level import DEFAULT_LOG_LEVEL, normalize_log_level

print(DEFAULT_LOG_LEVEL)                 # INFO
print(normalize_log_level(" debug "))    # DEBUG

try:
    normalize_log_level("VERBOSE")
except InvalidOptionError as error:
    print(error.field)    # log level
    print(error.allowed)  # 許可されるレベルのタプル

try:
    normalize_log_level(30)  # type: ignore[arg-type]
except ConfigurationError as error:
    print(error)  # log level must be a string, got 30.
```

## 実行方法

```bash
# すべて実行
pytest tests/runtime/test_log_level.py -v

# 正規化のケースのみ実行
pytest tests/runtime/test_log_level.py -k "uppercases" -v

# エラー分岐のケースのみ実行
pytest tests/runtime/test_log_level.py -k "rejects" -v
```

## 重要な詳細
- `normalize_log_level` はまず `isinstance` で厳密に文字列かどうかを判定するため、整数や `None` などの入力はレベル比較の分岐に入りません。
- 戻り値は必ず `LEVEL_DICT` 内の大文字キー名であり、呼び出し側はログフィルターのレベル設定にそのまま利用できます。
- すべてのケースはメモリ内の計算のみで、I/O の副作用はありません。

## 注意事項
- 関連実装は `src/celestialflow/runtime/util_log_level.py` にあります。`util_*` は実行エントリ内部のツールであり、`celestialflow.runtime` パッケージからは再エクスポートされません。
- 本ファイルでは `DEFAULT_LOG_LEVEL` に単独のアサーションを設けておらず、既定値はログレベルを必要とする実行エントリのパラメータ既定値として現れます。
