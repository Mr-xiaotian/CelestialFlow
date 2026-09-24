# tests/persistence/test_log.py

> 📅 最終更新日: 2026/09/24

## 役割
`celestialflow.persistence.core_log` の `LogInlet` と `LogSpout` を検証し、グラフライフサイクルイベント（起動/終了）、タスクリトライイベント、ノード起動イベントが非同期でバッチフラッシュされてログファイルに書き込まれ、正しいログレベルマーカーが保持されることを確認します。

## コアテスト対象

| クラス | 説明 |
|----|------|
| `LogInlet` | `log_level='INFO'` で初期化され、`graph_start()` / `task_retry()` / `graph_end()` / `node_start()` などの書き込みメソッドを提供 |
| `LogSpout` | バックグラウンドスレッドがキュー内のレコードをバッチでログファイルにフラッシュ。パスは `spout.log_path` で取得 |

## テストカバレッジマトリックス

| テストクラス | ケース数 | カバレッジ対象 |
|------------|---------|--------------|
| `TestLogPersistence` | 1 | 完全なログライフサイクル：graph_start → task_retry → graph_end → node_start。ログファイルに全内容とレベルマーカーが含まれることを検証 |

## 主要テストシナリオ

### `test_log_persistence`

- `graph_start("test_graph", "thread", ['test message'])` がグラフ起動メッセージを書き込み（引数順: グラフ名 / グラフモード / 構造リスト）。
- `task_retry('func', 'hello world', 1, ValueError('oops'), 0)` が例外情報付き WARNING レベルログを書き込み。
- `graph_end("test_graph", 1.0)` がグラフ終了イベントと経過時間を書き込み。
- `node_start('stage', 1, 'parallel-4')` がノード起動レコード（ノード名 / タスク数 / 実行モード記述）を書き込み。
- `wait_until` でログファイルの存在と `test message` や `hello world` などのキー内容を含むことをポーリング待機。
- 最終的にログファイルに `INFO` と `WARNING` の両方のレベルマーカーが存在することをアサート。

## 実行方法

```bash
pytest tests/persistence/test_log.py -v
pytest tests/persistence/test_log.py -k "log_persistence" -v
```

## 注意事項

- テストは `monkeypatch.chdir(tmp_path)` で作業ディレクトリを切り替え、ログファイルが一時パス下の `logs/` ディレクトリに書き込まれることを保証します。
- ログファイルの具体パスは `spout.log_path` 属性で取得します。
- 関連実装は `src/celestialflow/persistence/core_log.py` にあります。
