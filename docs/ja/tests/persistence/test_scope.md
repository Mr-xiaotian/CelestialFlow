# スコープ管理テスト (test_scope.py)

> 📅 最終更新日: 2026/08/26

## 役割

`celestialflow.persistence.core_scope` の `funnel_scope()` コンテキストマネージャがグローバルな LogSpout / LifecycleSpout のライフサイクルを自動管理することを検証し、スコープ進入時にバックグラウンドスレッドを起動し、退出時に正しくクリーンアップして永続化を完了することを確認します。

## コアテスト対象

- `funnel_scope()`: コンテキストマネージャ。グローバル log/lifecycle spout の起動と停止を自動管理。
- `get_log_spout()` / `get_lifecycle_spout()`: グローバルシングルトン spout を取得。
- `get_log_inlet()` / `get_lifecycle_inlet()`: 対応する inlet エントリを取得。

## テストカバレッジマトリックス

| テストクラス | ケース数 | カバレッジ対象 |
|------------|---------|------------|
| `TestFunnelScope` | 4 | ライフサイクル管理、再利用性、例外安全性、単層スコープのセマンティクス |

## 主要テストシナリオ

### `test_funnel_scope_starts_and_stops_global_spouts`

`funnel_scope()` 進入時に2つのグローバル spout のバックグラウンドスレッドが起動され、退出時に自動停止してスレッド参照がクリーンアップされることを検証。

- スコープ内で `log_spout._thread` と `lifecycle_spout._thread` が非 None かつ生存していることをアサート。
- `get_log_inlet().start_graph()` でログ書き込み、`get_lifecycle_inlet().task_in()` + `task_success()` で sqlite 書き込み。
- スコープ退出後、`_thread` が `None` であり、ログファイルと sqlite ファイルが永続化されて正しい内容を含むことをアサート。

### `test_funnel_scope_is_reusable`

`funnel_scope()` が複数回の独立した進入と退出をサポートすることを検証。

- 2 回進入/退出し、毎回進入時にスレッドが再作成され生存しており、退出後にスレッド参照が `None` であることをアサート。

### `test_funnel_scope_wraps_body_error_and_stops_spouts`

スコープ内部で例外がスローされた場合でも、`funnel_scope()` がクリーンアップを実行することを検証。

- `funnel_scope()` 内で `RuntimeError` をスロー。
- 例外が `ExceptionGroup` としてスローされることをアサート（`"Errors occurred during funnel scope"` にマッチ）。
- 退出後、2 つのグローバル spout の `_thread` がどちらも `None` であることをアサート。

### `test_funnel_scope_does_not_claim_nested_reuse`

現在の `funnel_scope()` が単層スコープであり、ネスト再利用のセマンティクスを検証しないことを確認。

- `funnel_scope()` を1回進入して簡単な操作を実行後に退出し、`_thread` がクリーンアップされていることをアサート。

## 実行方法

```bash
# 全部実行
pytest tests/persistence/test_scope.py -v

# キーワードでマッチ
pytest tests/persistence/test_scope.py -k "lifecycle" -v
pytest tests/persistence/test_scope.py -k "error" -v
pytest tests/persistence/test_scope.py -k "reusable" -v
```

## 注意事項

- 各ケースは autouse フィクスチャ `_cleanup_global_spouts` を使用して前後にグローバル spout をクリーンアップし、バックグラウンドスレッドとファイル状態の干渉を防ぎます。
- テストは `monkeypatch.chdir(tmp_path)` で作業ディレクトリを切り替え、ログと sqlite ファイルが一時パスに書き込まれることを保証します。
- 関連実装は `src/celestialflow/persistence/core_scope.py` にあります。
