# RuntimeConfig

> 📅 最終更新日: 2026/08/12

`runtime/util_config.py` はランタイム設定読み込み機能を提供し、現在はプロジェクトレベルの設定ファイルからログレベルを読み取るために使用されています。

## 主要関数

### load_log_level_from_pyproject

```python
def load_log_level_from_pyproject() -> str: ...
```

プロジェクトレベルの ``pyproject.toml`` の ``[tool.celestialflow]`` セクションから ``log_level`` を読み取ります。

- 現在の作業ディレクトリから上方向に ``pyproject.toml`` を検索します
- 見つからない場合は ``"INFO"`` を返します
- 見つかったが値が不正なレベルの場合は ``InvalidOptionError`` を送出します
- 解析に失敗した場合（TOML 形式エラー）は上方向の検索を続行します

### 戻り値

大文字の文字列（例: `"INFO"`、`"DEBUG"`）を返します。`util_constant.LEVEL_DICT` を用いて正当性を検証します。

## 使用例

```python
from celestialflow.runtime.util_config import load_log_level_from_pyproject

# 設定からログレベルを読み取る
level = load_log_level_from_pyproject()
print(f"現在のログレベル: {level}")
```

## 注意事項

- TOML 形式の設定ファイルのみサポートします
- ログレベルの有効な値は `util_constant.LEVEL_DICT` で定義されています（`TRACE` / `DEBUG` / `SUCCESS` / `INFO` / `WARNING` / `ERROR` / `CRITICAL`）
