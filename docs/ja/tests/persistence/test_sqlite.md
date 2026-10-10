# tests/persist/test_sqlite.py

> 📅 最終更新日: 2026/10/09

## 役割

`celestialflow.persist.util_sqlite` モジュールのすべての sqlite ユーティリティ関数を検証し、データベースのテーブル作成、レコードの CRUD、状態遷移、リトライ更新、ノード別集約などの機能が正確かつ信頼できることを確認します。

> 本テストファイルは歴史的な `test_splite.py` から改名されました。テストクラス名 `TestSpliteUtils` は歴史的な綴り（本来は `TestSqliteUtils`）を踏襲しており、ここではソースコードに合わせてそのまま残します。

## コアテスト対象

被テスト関数はすべて `celestialflow.persist.util_sqlite` 由来です：

| 関数 | 説明 |
|------|------|
| `connect_db` | 接続を確立し records テーブルとインデックスを自動作成。旧ライブラリでカラムが欠落している場合は `retry_times` を自動補完 |
| `normalize_record` | エラーレコードを sqlite 書き込み可能形式に正規化し、`node` または `status` が欠落している場合は `KeyError` を送出 |
| `insert_record` | レコードを1件挿入（メタ情報行は無視し、`False` を返す） |
| `load_records` | 任意の `status` パラメータで状態別にフィルタして全レコードを読み取り |
| `append_records` | レコードをバッチ追加（重複 event_id はスキップし、実際の書き込み件数を返す） |
| `query_records` | ページング、フィルタ、ソート検索（`page` / `page_size` / `node` / `keyword` / `sort_order`） |
| `query_error_type_counts` | エラータイプ別に failed レコード数を集計、`node` でフィルタ可能 |
| `clear_records` | records テーブルを全件クリア |
| `get_max_event_id_in_fail` | failed 状態のみの最大 event_id を集計。レコードがない場合は `None` を返す |
| `load_records_after_event_id_in_fail` | failed event_id 下限で増分読み取り |
| `promote_record_to_failed_by_event_id` | 状態を failed に更新しエラー情報を書き込み（`event_id` はエラーイベント ID に置き換え） |
| `promote_record_to_success_by_event_id` | 状態を success に更新し結果を書き込み |
| `update_retry_by_event_id` | pending レコードのリトライ回数とエラー情報を更新し、状態は変更しない。レコードが存在しない場合は `False` を返す |
| `delete_record_by_event_id` | event_id でレコードを削除 |
| `load_task_error_records` | ノード別に `(task_json, (error_type, error_message))` リストを読み取り |
| `load_task_result_records` | ノード別に `(task_json, result_json)` リストを読み取り |

## テストカバレッジマトリックス

| テストクラス | ケース数 | カバレッジ対象 |
|--------|--------|---------|
| `TestSpliteUtils` | 19 | 接続・テーブル作成、正規化、挿入/読み取り、追加/重複排除、ページング検索、クリア、増分/グループ読み取り、エラータイプ集計、状態遷移、リトライ更新、削除、ペア読み取り |

## 主要テストシナリオ

### テーブル作成とインデックス

- `connect_db` は `records` テーブルおよび `idx_records_event_id`、`idx_records_status_id` インデックスを自動作成。
- `result_json` フィールドの存在を検証し、テーブル構造のフィールド順序が `id / event_id / ts / node / status / error_type / error_message / task_json / result_json / retry_times` であることを確認。

### 正規化

- `event_id` を欠くメタ情報行（例：`timestamp` / `graph_name` のみ）は `None` を返し、データベースに保存されない。
- 業務レコードが `node` または `status` を欠く場合、`normalize_record` は `KeyError` を送出。
- エラーレコードは `status="failed"` に正規化され、`retry_times` はデフォルトで 0、`task_json` は JSON 文字列にシリアライズされる。

### 挿入と読み取り

- メタ情報行の `insert_record` は `False` を返し、書き込まれない。
- `load_records` は `status`（例：`"failed"` / `"success"`）でフィルタ可能。
- `load_records` で読み戻す際、`task_json` / `result_json` フィールドは Python オブジェクトにデシリアライズされる。

### 追加と重複排除

- `append_records` は既存の `event_id` をスキップし、繰り返し同期の冪等性を保証。
- 戻り値は実際に書き込まれたレコード数。

### ページング検索

- `query_records` は `page` / `page_size` / `node` / `keyword` / `sort_order` パラメータをサポート。
- `newest` / `oldest` 並び替えおよび `keyword` によるあいまい一致を検証。
- 戻り値はタプル `(total, total_pages, page_items)`。

### エラータイプ集計

- `query_error_type_counts` はエラータイプ（`error_type`）別に全 failed レコード数を集計し、`count` の降順でソート。
- `query_error_type_counts` は `node` パラメータによるノードフィルタをサポート。
- status が `failed` のレコードのみを集計し、success など他の状態は無視。

### 状態遷移とリトライ更新

- `promote_record_to_failed_by_event_id`: waiting→failed、event_id を新しいエラーイベント ID に移行しエラー情報を書き込み。
- `promote_record_to_success_by_event_id`: pending→success、結果を書き込み、元の event_id を保持。
- `update_retry_by_event_id`: pending レコードのリトライ回数とエラー情報を更新し、状態は pending のまま維持。存在しない event_id に対しては `False` を返す。

### 増分とグループ化

- `get_max_event_id_in_fail` は failed 状態のみを集計。failed レコードがない場合は `None` を返す。
- `load_records_after_event_id_in_fail` は event_id 下限で増分読み取り。
- `load_task_error_records` はノードフィルタをサポートし、`(task_json, (error_type, error_message))` リストを返す。

### ペア読み取り

- `load_task_result_records` はノードでフィルタ可能な `(task_json, result_json)` リストを返す。

## 実行方法

```bash
# 全部実行
pytest tests/persist/test_sqlite.py -v

# キーワードでマッチ
pytest tests/persist/test_sqlite.py -k "connect or normalize" -v
pytest tests/persist/test_sqlite.py -k "insert or append" -v
pytest tests/persist/test_sqlite.py -k "promote or retry" -v
pytest tests/persist/test_sqlite.py -k "group" -v
pytest tests/persist/test_sqlite.py -k "load_task" -v
```

## 注意事項

- テストは `tmp_path` fixture を使用して一時 sqlite ファイルを作成し、テスト終了後に自動クリーンアップされます。
- `sample_errors` fixture は 3 件の有効なエラーレコード + 1 件のメタ情報行をテストデータセットとして提供し、`sqlite_path` fixture は `tmp_path / "records.sqlite3"` パスを提供します。
- sqlite `records` テーブルのノード識別フィールドは `node`（リファクタリング前は `stage`）。ノード別に読み取り / フィルタするすべての関数は `node` を基準とします。
- 関連実装は `src/celestialflow/persist/util_sqlite.py` にあります。