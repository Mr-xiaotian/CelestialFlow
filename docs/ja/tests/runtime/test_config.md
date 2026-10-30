# tests/runtime/test_config.py

> 📅 最終更新日: 2026/10/30

## 役割
`celestialflow.runtime.ReportConfig` の構築時検証とアドレス正規化を検証します。デフォルトアドレスへのフォールバック、先頭・末尾の空白および末尾スラッシュの除去、さらに非文字列・空文字列・不正なスキームといった不正入力が `ConfigurationError` で拒否されるかどうかを確認します。あわせて、設定オブジェクトが不変であることも検証します。

## コアテスト対象
- `ReportConfig`: 凍結された dataclass（`frozen=True, slots=True`）。唯一のフィールドは `url` で、構築時に `__post_init__` 内で検証と正規化を行います。
- `DEFAULT_REPORT_URL`: アドレスを明示的に指定しない場合に使用されるデフォルトの報告先（`http://127.0.0.1:5005`）。`celestialflow.runtime` パッケージから再エクスポートされます。
- `ConfigurationError`: 不正なアドレスに対して一律で送出されるカスタム設定例外。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|--------|--------|---------|
| `TestReportConfig` | 6 | デフォルトアドレス、空白と末尾スラッシュの正規化、空文字列の拒否、`http`/`https` 以外のスキームの拒否、非文字列の拒否、オブジェクトの凍結 |

## 主要テストシナリオ

### `TestReportConfig`
1. **デフォルトアドレス** (`test_default_url`): 引数なしで構築した `ReportConfig().url == DEFAULT_REPORT_URL`。
2. **スラッシュ除去後のアドレスへの正規化** (`test_strips_whitespace_and_trailing_slash`): `ReportConfig(url=" http://127.0.0.1:9000/ ")` の `url` は `"http://127.0.0.1:9000"` となり、報告エンドポイントとの結合で二重スラッシュが生じるのを防ぎます。
3. **空白文字列の拒否** (`test_rejects_empty_url`): `url="   "` は空白除去後に空になるため、`ConfigurationError` を送出します。
4. **HTTP 以外のスキームの拒否** (`test_rejects_non_http_scheme`): `url="ftp://127.0.0.1:9000"` は `ConfigurationError` を送出します。
5. **非文字列の拒否** (`test_rejects_non_string_url`): `url=5005` は `ConfigurationError` を送出します。
6. **不変性** (`test_is_frozen`): 構築後に `url` へ代入すると `AttributeError` を送出します。

## テストの重点
- **起動前検証**: アドレスは `ReportConfig` の構築段階で検証が完了するため、不正な設定は実行時のリソース起動より前に失敗します。
- **正規化**: 先頭・末尾の空白は `strip()`、末尾スラッシュは `rstrip("/")` で除去され、エンドポイントの結合パスが安定します。
- **明示的な有効化の意味論**: 報告の有効・無効は、実行エントリに `ReportConfig` を渡すかどうかで決まります。`ReportConfig` 自体はもはや「スイッチ + アドレス」の複合設定ではありません。
- **明確な失敗モード**: すべての不正アドレスは `ConfigurationError` で拒否され、デフォルト値へ暗黙にフォールバックすることはありません。

## 実行方法

```bash
# すべて実行
pytest tests/runtime/test_config.py -v

# デフォルトアドレスと正規化のケースのみ実行
pytest tests/runtime/test_config.py -k "default_url or strips_whitespace" -v

# 不正入力と凍結関連のケースのみ実行
pytest tests/runtime/test_config.py -k "rejects or frozen" -v
```

## 重要な詳細
- 実装では `url` を `urlsplit` で検証します。スキームは `http` / `https` でなければならず、`netloc` が存在する必要があります（`http://` のようにホストを欠くアドレスも同様に拒否されます）。テストケースでは `ftp://` を用いてスキーム不正の分岐をカバーしています。
- `slots=True` かつ `frozen=True` であるため、インスタンスは動的に属性を追加できず、構築後に `url` を書き換えることもできません。
- すべてのケースはメモリ内での構築のみで、ファイルやネットワークの副作用はありません。

## 注意事項
- 関連実装は `src/celestialflow/runtime/core_config.py` にあり、公開シンボルは `src/celestialflow/runtime/__init__.py` から再エクスポートされます。
- ホストプロジェクトの `pyproject.toml` はもはや報告設定の読み取りに関与せず、設定は呼び出し側が明示的に渡す必要があります。
