# tests/runtime/test_config.py

> 📅 最終更新日: 2026/10/09

## 役割

`celestialflow.runtime.util_config` の `load_report_url_from_pyproject` と `load_if_report_from_pyproject` の 2 つの関数を検証します。プロジェクトレベルの `pyproject.toml` の `[tool.celestialflow]` セクションから報告アドレスと報告スイッチを正しく読み取れること、および設定が欠落または不正な場合にデフォルト値へフォールバックできること / `ConfigurationError` を送出することを確認します。

## コアテスト対象

- `load_report_url_from_pyproject()`: `report_url` を読み取り。未設定または `pyproject.toml` がない場合は `DEFAULT_REPORT_URL`（`http://127.0.0.1:5005`）を返す。
- `load_if_report_from_pyproject()`: `if_report` を読み取り。未設定または `pyproject.toml` がない場合は `False` を返す。非ブール値が設定されている場合は `ConfigurationError` を送出。
- `DEFAULT_REPORT_URL`: 報告アドレスのデフォルト定数。設定がない場合のフォールバック値。

## テスト補助

- `tmp_path` + `monkeypatch.chdir`: 一時ディレクトリに `pyproject.toml` を書き込んだ後に被テスト関数を呼び出し、実際の作業ディレクトリへの依存を隔離。

## 主要テストシナリオ

### `load_report_url_from_pyproject`
1. **設定済みアドレスの読み取り** (`test_load_report_url_reads_report_url`): `pyproject.toml` に `report_url = "http://127.0.0.1:9000"` が設定されている場合、そのアドレスを返す。
2. **未設定時のデフォルト値** (`test_load_report_url_defaults_when_absent`): `log_level` のみで `report_url` がない場合、`DEFAULT_REPORT_URL` を返す。
3. **`pyproject.toml` なし** (`test_load_report_url_defaults_without_pyproject`): 空ディレクトリで `DEFAULT_REPORT_URL` を返す。

### `load_if_report_from_pyproject`
1. **設定済みスイッチの読み取り** (`test_load_if_report_reads_true`): `if_report = true` の場合 `True` を返す。
2. **未設定時はデフォルトでオフ** (`test_load_if_report_defaults_to_false`): `report_url` のみで `if_report` がない場合 `False` を返す（スイッチとアドレスはデカップリングされている）。
3. **`pyproject.toml` なし** (`test_load_if_report_returns_false_without_pyproject`): 空ディレクトリで `False` を返す。
4. **非ブール設定でエラー** (`test_load_if_report_rejects_non_boolean`): `if_report = "yes"` の場合 `ConfigurationError` を送出。

## テストの重点

- **デフォルトフォールバック**: 報告アドレスとスイッチは、設定が欠落している場合に明確なデフォルト値を持つ。
- **スイッチのデカップリング**: `report_url` の存在が報告を暗黙的に有効にすることはない。`if_report` は明示的に `true` である必要がある。
- **不正入力**: `if_report` が非ブール値の場合、静かに無視するのではなく `ConfigurationError` で拒否する。

## 実行方法

```bash
# 全部実行
pytest tests/runtime/test_config.py -v

# 報告アドレス関連テストのみ実行
pytest tests/runtime/test_config.py -k "report_url" -v

# 報告スイッチ関連テストのみ実行
pytest tests/runtime/test_config.py -k "if_report" -v
```

## 注意事項

- 関連実装は `src/celestialflow/runtime/util_config.py` にあります。
- すべてのケースは `monkeypatch.chdir` で作業ディレクトリを切り替えるため、テストは高速で実際のネットワーク / ファイル副作用がありません。