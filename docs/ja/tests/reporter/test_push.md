# tests/reporter/test_push.py

> 📅 最終更新日: 2026/11/13

## 役割

`celestialflow.reporter.core_push` のプッシュ経路を検証します：

- `PushInlet.on_event(event)` は `match` で `GraphStartEvent` / `GraphEndEvent` / `TaskFailEvent` を対応する `kind` の `PushRecord` へマッピングし、`send()` でエンキューする；
- `PushSpout` はレコード種別に応じてレコードを異なるエンドポイントへ POST し、2xx 以外では `ReporterError` を送出する；
- バックグラウンドスレッドがキューを消費し、単一レコードの失敗でスレッドは死なず、`stop()` 時に HTTP セッションをクローズする；
- `NullPushSpout` は HTTP セッションを確立せず、レコードを直接破棄する。

## コアテスト対象

| オブジェクト | ソース | 説明 |
|------|------|------|
| `PushInlet` | `celestialflow.reporter` | オブザーバー入口 `on_event()` + エンキュー用メソッド `send()`；さらに `push_snapshot()` を含む |
| `PushSpout` | `celestialflow.reporter` | プッシュ spout。`PushRecord` キューの消費者 |
| `NullPushSpout` | `celestialflow.reporter` | 空実装の spout |
| `PushRecord` | `celestialflow.reporter.core_push` | frozen dataclass。`kind` に応じて異なるフィールドを再利用する |
| `GraphStartEvent` / `GraphEndEvent` / `TaskFailEvent` | `celestialflow.observer` | エンキューマッピングの対象となる 3 種類のイベント |
| `ReporterError` | `celestialflow.runtime.util_errors` | 2xx 以外のレスポンスに対する想定例外 |
| `wait_until` | `tests/conftest.py` | バックグラウンドスレッドの消費完了をポーリング待機する（デフォルト 5 秒タイムアウト） |

## 主要 fixture とフェイクオブジェクト

| 名前 | 用途 |
|------|------|
| `FakePostResponse` | レスポンスを模擬：`ok` と `status_code` を設定可能 |
| `FakePushSession` | `requests.Session` の代替：`post()` が `(url, json, timeout)` を記録し、`close()` が `closed = True` にする |
| `_fail_event(...)` | `TaskFailEvent(node, task, f"({task})", exception, task_id=1, error_id)` を構築。デフォルトは `error_id=21`、`node="s1"`、`task="data1"`、`ValueError("oops")` |
| `_start_event()` | グラフメタ情報付きの `GraphStartEvent` を構築（`g1` / `thread` / `is_dag=True` / 2 ノードと `node_meta`） |
| `_end_event()` | `GraphEndEvent(graph="g1", end_time=456.0, elapsed=1.5)` を構築 |
| `_dequeue(spout)` | `spout.get_queue()` からレコードを 1 件取り出し、型が `PushRecord` であることをアサートする |

## テストカバレッジマトリックス

| ケース | カバレッジ目標 |
|------|---------|
| `test_inlet_maps_task_fail_event` | 失敗イベント → `kind="task_fail"`、`event_id` / `node` / `task_json` / `error_type` / `error_message` / `ts` |
| `test_inlet_maps_graph_start_event` | グラフ開始イベント → `kind="graph_start"`、グラフメタフィールドが完全に透過する |
| `test_inlet_maps_graph_end_event` | グラフ終了イベント → `kind="graph_end"`、`end_time` / `elapsed` |
| `test_spout_pushes_task_fail_to_push_error_endpoint` | `POST /api/push_error` とペイロードのフィールド |
| `test_spout_pushes_graph_start_to_graph_meta_endpoint` | `POST /api/push_graph_meta` とトップレベルのグラフメタフィールド |
| `test_spout_pushes_graph_end_to_shutdown_endpoint` | `POST /api/shutdown_session`、ペイロードは `session_id` のみ |
| `test_handle_record_raises_reporter_error_on_failure` | 2xx 以外のとき `_handle_record` が `ReporterError` を送出する |
| `test_spout_thread_drains_records_and_closes_session` | バックグラウンドスレッドが 2 件のレコードを消費し、キューが空になり、`stop()` 後にセッションがクローズされる |
| `test_spout_thread_survives_push_failure` | 継続的な失敗でもスレッドは死なず、レコードは消費され、スレッドは正常に停止できる |
| `test_null_spout_discards_records` | `NullPushSpout` は session を生成せず、レコードは排出される |

## 主要な挙動の詳細

### イベント → レコードマッピング

| イベント | `PushRecord.kind` | 使用フィールド |
|------|-------------------|---------|
| `GraphStartEvent` | `"graph_start"` | `graph`、`graph_mode`、`start_time`、`is_dag`、`nodes`、`edges`、`source_nodes`、`node_meta` |
| `GraphEndEvent` | `"graph_end"` | `graph`、`end_time`、`elapsed` |
| `TaskFailEvent` | `"task_fail"` | `event_id ← error_id`、`node`、`task_json ← to_persisted_payload(task)`、`error_type ← exception の型名`、`error_message ← str(exception)`、`ts ← time.time()` |
| その他のイベント | エンキューしない | `match` の `case _: pass` |

- `PushInlet` は `BaseInlet` と `Observer` を継承し、イベント入口は `on_event(event)` に統一されています；レコードのエンキューは `send()` に統一（`BaseInlet` が提供し、バインドされた spout のキューへ書き込む）。
- `task_json` は `to_persisted_payload` を通るため、テスト内の `task={"value": 1}` は同型の辞書になります；シリアライズできないオブジェクトは永続化可能な形へ投影されます。
- `error_id` はレコード内でのフィールド名が `event_id` です。

### レコード → エンドポイント

| `kind` | エンドポイント | ペイロードの要点 |
|--------|------|---------|
| `graph_start` | `{base_url}/api/push_graph_meta` | `session_id` + すべてのグラフメタフィールド（トップレベルに展開） |
| `graph_end` | `{base_url}/api/shutdown_session` | `{"session_id": ...}` のみで、`end_time` / `elapsed` は**送信しない** |
| `task_fail` | `{base_url}/api/push_error` | `session_id`、`event_id`、`node`、`task_json`、`error_type`、`error_message`、`ts` |
| `snapshot` | `{base_url}/api/push_snapshot` | `test_snapshot.md` を参照 |

- テストは `payload["timestamp"]` のようなフィールドを本ファイルの範囲ではアサートしません；本ファイルは上記 3 種類のイベントレコードのみをカバーします。
- `graph_end` の意味論は「セッションのオフライン通知」です：サーバは受信後にセッションを終了としてマークしますが、セッションデータとエラーライブラリは引き続き保持されます。
- 各 POST は `timeout=self.timeout`（構築時のデフォルト `3.0`）を伴います；テストは `_timeout` として受け取るだけで、アサートを書き換えません。

### バックグラウンドスレッドと失敗の隔離

- `PushSpout.start()` は `BaseSpout._before_start()` で `requests.Session` を生成し、その後 daemon スレッドを起動して `get_queue()` をループします。
- `_handle_record` が送出する `ReporterError` は `BaseSpout._spout` の `try/except Exception` に捕捉されて出力され、スレッドは消費を続けます；`get_pending_count()` は `finally` 内でデクリメントされます。
- `stop()` はキューへ終了シグナルを投入して `join`（最大 5 秒）し、スレッド終了後に `_after_stop()` が session をクローズします。
- スレッドのケースは `monkeypatch.setattr(push_module.requests, "Session", lambda: session)` でフェイクセッションを注入し、`wait_until(lambda: len(session.posts) == 2 and spout.get_pending_count() == 0)` で消費完了を待ちます。
- `test_spout_thread_survives_push_failure` は `ok=False` のセッションを使用し、`get_pending_count() == 0` のみを待って最後に `session.closed` をアサートし、失敗が停止をブロックしないことを証明します。

### Null 版

`NullPushSpout` は `_handle_record` を直接破棄するよう上書きし、`_before_start` を上書きしないため、`requests.Session` を一切生成しません。テストは `requests.Session` を `pytest.fail(...)` に置き換え、呼ばれれば即座に失敗するようにします；その後起動し、2 件のレコードをエンキューしてキューが空になるのを待ち、停止します。

## 実行方法

```bash
# すべて実行
uv run pytest tests/reporter/test_push.py -v

# エンキューマッピングのみ
uv run pytest tests/reporter/test_push.py -k "inlet_maps" -v

# エンドポイントへのプッシュのみ
uv run pytest tests/reporter/test_push.py -k "endpoint" -v

# バックグラウンドスレッドのみ
uv run pytest tests/reporter/test_push.py -k "thread or null" -v
```

## 注意事項

- スレッドを使わないケースは `spout._session` に直接フェイクセッションを代入して `start()` を迂回します；これは被テスト実装のプライベートフィールド名 `_session` に依存するため、リネーム時にはテストも同期して変更する必要があります。
- スレッドのケースは `tests/conftest.py` の `wait_until`（ルート `conftest` 経由でインポート）に依存し、デフォルトのタイムアウトは 5 秒です；実際の所要時間はこれを大きく下回るはずです。
- キューにはエンキュー済みだが未消費のレコードが残る可能性があるため、テストは `spout.get_queue().get()` で同期的に取り出し、スレッドを起動しません。
- 関連実装は `src/celestialflow/reporter/core_push.py`、意味論の説明は `docs/zh-CN/src/reporter/core_push.md` を参照してください。
