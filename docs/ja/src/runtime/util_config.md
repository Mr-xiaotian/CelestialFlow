# src/celestialflow/runtime/util_config.py

> 📅 最終更新日: 2026/10/09

`runtime/util_config.py` はランタイム設定読み込み機能を提供し、プロジェクトレベルの `pyproject.toml` の `[tool.celestialflow]` セクションからログレベル、レポートアドレス、レポートスイッチを読み取ります。

## デフォルト定数

### DEFAULT_REPORT_URL

`report_url` が未設定の場合に使用されるデフォルトのレポートアドレス `"http://127.0.0.1:5005"`。

## 主要関数

### load_log_level_from_pyproject

```python
def load_log_level_from_pyproject() -> str: ...
```

プロジェクトレベルの `pyproject.toml` の `[tool.celestialflow]` セクションから `log_level` を読み取ります。

- 現在の作業ディレクトリから上方向に `pyproject.toml` を検索します
- 見つからない場合は `"INFO"` を返します
- 見つかったが値が不正なレベルの場合は `InvalidOptionError` を送出します
- 解析に失敗した場合（TOML 形式エラー）は上方向の検索を続行します

大文字の文字列（例: `"INFO"`、`"DEBUG"`）を返します。`util_constant.LEVEL_DICT` を用いて正当性を検証します。

### load_report_url_from_pyproject

```python
def load_report_url_from_pyproject() -> str: ...
```

プロジェクトレベルの `pyproject.toml` の `[tool.celestialflow]` セクションから `report_url` を読み取ります。

- 現在の作業ディレクトリから上方向に `pyproject.toml` を検索します
- 対応する設定が見つからない場合はデフォルトアドレス `DEFAULT_REPORT_URL` を返します
- 解析に失敗した場合（TOML 形式エラー）は上方向の検索を続行します

### load_if_report_from_pyproject

```python
def load_if_report_from_pyproject() -> bool: ...
```

プロジェクトレベルの `pyproject.toml` の `[tool.celestialflow]` セクションから `if_report` を読み取ります。

- 現在の作業ディレクトリから上方向に `pyproject.toml` を検索します
- 未設定の場合は `False` を返します
- レポートスイッチとレポートアドレスは分離されています：明示的に `true` と設定された場合のみレポートが有効になり、`report_url` の存在自体ではレポートはトリガーされません
- 設定値がブール値でない場合は `ConfigurationError` を送出します
- 解析に失敗した場合（TOML 形式エラー）は上方向の検索を続行します

## 使用例

```python
from celestialflow.runtime.util_config import (
    DEFAULT_REPORT_URL,
    load_log_level_from_pyproject,
    load_report_url_from_pyproject,
    load_if_report_from_pyproject,
)

# 設定からログレベルを読み取る
level = load_log_level_from_pyproject()
print(f"現在のログレベル: {level}")

# レポートアドレスとスイッチ
url = load_report_url_from_pyproject()
if_report = load_if_report_from_pyproject()
print(f"レポートアドレス: {url}（デフォルト {DEFAULT_REPORT_URL}）、有効か: {if_report}")
```

## 注意事項

- TOML 形式の設定ファイルのみサポートします
- ログレベルの有効な値は `util_constant.LEVEL_DICT` で定義されています（`TRACE` / `DEBUG` / `SUCCESS` / `INFO` / `WARNING` / `ERROR` / `CRITICAL`）