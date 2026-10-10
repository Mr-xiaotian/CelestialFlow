# tests/persist/test_log.py

> 📅 最終更新日: 2026/10/09

## 役割

`celestialflow.persist.core_log` の `LogInlet` と `LogSpout` を検証し、グラフライフサイクルイベント（起動 / 終了）、ノード起動イベント、タスクリトライイベント、スキップイベントが非同期でバッチフラッシュされてログファイルに書き込まれ、正しいログレベルマーカーが保持されることを確認します。

## コアテスト対象

| クラス / オブジェクト | ソース | 説明 |
|-----------|------|------|
| `LogInlet` | `celestialflow.persist.core_log` | `MetricsObserver` と `log_level` で初期化され、`on_graph_start` / `on_task_retry` / `on_graph_end` / `on_node_start` / `on_task_skip` などのイベント書き込みメソッドを提供 |
| `LogSpout` | `celestialflow.persist.core_log` | バックグラウンドスレッドがキュー内のレコードをバッチでログファイルにフラッシュ。パスは `spout.log_path` で取得 |
| `MetricsObserver` | `celestialflow.observer` | LogInlet がノード指標をクエリしてログ内容を生成するために使用 |
| イベント型 | `celestialflow.observer` | `GraphStartEvent` / `TaskRetryEvent` / `GraphEndEvent` / `NodeStartEvent` / `TaskSkipEvent` |

## テストカバレッジマトリックス

| テストクラス | ケース数 | カバレッジ対象 |
|--------|--------|---------|
| `TestLogPersistence` | 2 | 完全なログライフサイクル、スキップログ |

## 主要テストシナリオ

### `test_log_persistence`

- `LogInlet(MetricsObserver(), log_level='INFO').bind_spout(spout)` を構築し、`spout.start()` でバックグラウンドスレッドを起動。
- 順に `on_graph_start`（グラフ名 / モード / 構造リスト / ノードメタ情報）、`on_task_retry`（例外を保持 → WARNING レベル）、`on_graph_end`、`on_node_start` をトリガー。
- `wait_until` でログファイルの存在と、`| node |` や `hello world` などのキー内容を含むことをポーリング待機。
- 最終的にログファイルに `INFO` と `WARNING` の両方のレベルマーカーが存在することをアサート。

### `test_skip_log`

- `LogInlet(MetricsObserver(), log_level='SUCCESS').bind_spout(spout)` を構築。
- `on_task_skip`（`[7->8*]` のイベント ID 区間マーカーを保持）をトリガー。
- ログファイルに `hello world`、`skipped`、`[7->8*]` と `SUCCESS` レベルマーカーが含まれることをアサート。

## 実行方法

```bash
pytest tests/persist/test_log.py -v
pytest tests/persist/test_log.py -k "log_persistence" -v
pytest tests/persist/test_log.py -k "skip" -v
```

## 注意事項

- テストは `monkeypatch.chdir(tmp_path)` で作業ディレクトリを切り替え、ログファイルが一時パス下の `logs/` ディレクトリに書き込まれることを保証します。
- ログファイルの具体パスは `spout.log_path` 属性で取得します。
- `LogInlet` は `bind_spout` で `LogSpout` にバインドされ、イベントはキュー経由で非同期にファイルへ書き込まれます。
- 関連実装は `src/celestialflow/persist/core_log.py` にあります。