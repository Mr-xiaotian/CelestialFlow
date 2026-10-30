# tests/persist/test_sqlite.py

> 📅 最終更新日: 2026/10/30

## 役割

`celestialflow.persist.util_sqlite` の sqlite ユーティリティ関数を検証し、テーブルとインデックスの作成、レコードの正規化、単一挿入、状態遷移（failed / success）、リトライ情報の更新、event_id による削除、ノード別ペア読み取りなどの機能が正確かつ信頼できることを確認します。

> 本テストファイルは歴史的な `test_splite.py` から改名されました。テストクラス名 `TestSpliteUtils` は歴史的な綴り（本来は `TestSqliteUtils`）を踏襲しており、ここではソースコードに合わせてそのまま残します。

## コアテスト対象

被テスト関数はすべて `celestialflow.persist.util_sqlite` 由来です：

| 関数 | 説明 |
|------|------|
| `connect_db` | 接続を確立し（`check_same_thread=False`、WAL、`synchronous=NORMAL`）、records テーブルとインデックスを自動作成。旧ライブラリでカラムが欠落している場合は `retry_times` を自動補完 |
| `normalize_record` | レコードを sqlite 書き込み可能形式に正規化する；`event_id` を持たないメタ情報行は `None` を返し、業務レコードが `node` または `status` を欠く場合は `KeyError` を送出 |
| `insert_record` | 既存の接続上にレコードを 1 件挿入する。メタ情報行は `False`、実際に挿入した場合は `True` を返す |
| `row_to_record_dict` | `sqlite3.Row` を対外的なレコード辞書に変換し、`task_json` / `result_json` を Python オブジェクトにデシリアライズする |
| `promote_record_to_failed_by_event_id` | 状態を failed に更新し、`event_id` をエラーイベント ID に置き換え、エラー情報とタイムスタンプを書き込む |
| `promote_record_to_success_by_event_id` | 状態を success に更新し、結果とタイムスタンプを書き込み、元の `event_id` を保持する |
| `update_retry_by_event_id` | レコードのリトライ回数と直近のエラー情報を更新し、状態は変更しない；レコードが存在しない場合は `False` を返す |
| `delete_record_by_event_id` | event_id でレコードを削除する |
| `load_task_error_records` | ノード別に `(task_json, (error_type, error_message))` リストを読み取る |
| `load_task_result_records` | ノード別に `(task_json, result_json)` リストを読み取る |

本ファイルにはさらに 2 つのテスト補助関数（被テスト対象ではない）が定義されています：

| 補助関数 | 説明 |
|----------|------|
| `_insert_records(sqlite_path, records)` | `connect_db` + `insert_record` で 1 件ずつ書き込み、`sqlite3.IntegrityError`（`event_id` の重複）が発生した場合はスキップし、実際に書き込んだ件数を返す |
| `_fetch_records(sqlite_path, status)` | `connect_db` で `status` 別にクエリし、`row_to_record_dict` で辞書リストに変換してアサーション用に読み取る |

## テストカバレッジマトリックス

| テストクラス | ケース数 | カバレッジ対象 |
|--------|--------|---------|
| `TestSpliteUtils` | 11 | 接続とテーブル/インデックス作成、正規化、挿入と読み取り、failed / success の状態遷移、リトライ更新（レコード欠落を含む）、event_id による削除、ノード別ペア読み取り |

## 主要テストシナリオ

### テーブル作成とインデックス

- `connect_db` は `records` テーブル、`idx_records_event_id`（ユニーク）、`idx_records_status_id` インデックスを自動作成。
- `PRAGMA index_list(records)` で `idx_records_event_id` がユニークインデックスであることを確認。
- テーブル構造のフィールド順序が `id / event_id / ts / node / status / error_type / error_message / task_json / result_json / retry_times` であることを照合し、`result_json` フィールドが存在することを確認。

### 正規化

- `event_id` を欠くメタ情報行（例：`timestamp` / `graph_name` のみ）は `normalize_record` が `None` を返す。
- 業務レコードが `node` または `status` を欠く場合は `KeyError` を送出し、メッセージ中のフィールド名と一致する。
- 有効なレコードは `event_id` / `node` / `status` / `error_type` / `error_message` / `ts` / `retry_times` などのフィールドに正規化され、`retry_times` はデフォルト 0、`task_json` は JSON 文字列にシリアライズされる。

### 挿入と読み取り

- メタ情報行の `insert_record` は `False` を返し書き込まれない；2 件の有効なレコードは `True` を返す。
- `_fetch_records` が `row_to_record_dict` 経由で読み戻す際、`task_json` は Python オブジェクトにデシリアライズされ、`result_json` は `None`、`id` は挿入順に自動増加する。

### 状態遷移

- `promote_record_to_failed_by_event_id`: waiting レコード（`event_id=9`）から新しいエラーイベント ID（19）へ移行し、`status="failed"`、`ts=9.5`、`error_type="RuntimeError"`、`error_message="boom"` を書き込み、`True` を返す。
- `promote_record_to_success_by_event_id`: pending レコード（`event_id=8`）を success に昇格させ、元の `event_id` を保持し、`ts=8.5` と `result_json` を書き込み、`task_json` は変化しない。

### リトライ更新

- `update_retry_by_event_id`: pending レコードに `retry_times=2`、`ts`、`error_type` / `error_message` を書き込み、状態は `pending` のまま、`True` を返す。
- 存在しない `event_id=999` への更新は `False` を返す。

### 削除

- `delete_record_by_event_id(conn, 2)` は `True` を返し、残った failed レコードの `event_id` は `[1, 3]`。

### ペア読み取り

- `load_task_error_records(db_path, "s1")` は s1 の failed レコードのみを `id` 昇順で返し、要素は `(task_json, (error_type, error_message))`。
- `load_task_result_records(db_path, "s8")` は `[(task_json, result_json)]` を返す。

## 実行方法

```bash
# 全部実行
pytest tests/persist/test_sqlite.py -v

# キーワードでマッチ
pytest tests/persist/test_sqlite.py -k "connect or normalize" -v
pytest tests/persist/test_sqlite.py -k "insert" -v
pytest tests/persist/test_sqlite.py -k "promote or retry" -v
pytest tests/persist/test_sqlite.py -k "delete" -v
pytest tests/persist/test_sqlite.py -k "load_task" -v
```

## 注意事項

- テストは `tmp_path` fixture を使用して一時 sqlite ファイルを作成し、テスト終了後に自動クリーンアップされます。
- `sample_errors` fixture は 3 件の有効なエラーレコード + 1 件のメタ情報行をテストデータセットとして提供し、`sqlite_path` fixture は `tmp_path / "records.sqlite3"` パスを提供します。
- すべての書き込み操作は `connect_db` が返す接続上で実行され、テスト自身が `commit()` と `close()` を行います。
- sqlite `records` テーブルのノード識別フィールドは `node` であり、ノード別に読み取り / フィルタするすべての関数は `node` を基準とします。
- 関連実装は `src/celestialflow/persist/util_sqlite.py` にあります。
