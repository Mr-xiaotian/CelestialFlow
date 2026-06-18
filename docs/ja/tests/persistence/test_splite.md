# SQLite ユーティリティテスト (test_splite.py)

> 最終更新日: 2026/06/18

## 目的

`celestialflow.persistence.util_sqlite` モジュールのすべての sqlite ユーティリティ関数を検証し、データベースのテーブル作成、レコードの CRUD、状態遷移、stage 別集約などの機能が正確かつ信頼できることを確認します。

## コアテスト対象

| 関数 | 説明 |
|------|------|
| `connect_db` | 接続を確立し、records テーブルとインデックスを自動作成 |
| `normalize_record` | エラーレコードを sqlite 書き込み可能形式に正規化 |
| `insert_record` | レコードを1件挿入（メタ情報行は無視） |
| `load_records` | ステータスでフィルタして全レコードを読み取り |
| `append_records` | レコードをバッチ追加（重複 event_id はスキップ） |
| `query_records` | ページング、フィルタ、ソート検索 |
| `clear_records` | records テーブルを全件クリア |
| `get_max_event_id_in_fail` | failed 状態のみの最大 event_id を集計 |
| `load_records_after_event_id_in_fail` | failed event_id 下限で増分読み取り |
| `load_records_grouped_by_stage` | stage 別に failed レコードをグループ化読み取り |
| `promote_record_to_failed_by_event_id` | ステータスを failed に更新しエラー情報を書き込み |
| `promote_record_to_success_by_event_id` | ステータスを success に更新し結果を書き込み |
| `update_record_event_id_by_event_id` | レコードの event_id を移行 |
| `delete_record_by_event_id` | event_id でレコードを削除 |
| `load_task_error_records` | stage 別に task-error ペアを読み取り |
| `load_task_result_records` | stage 別に task-result ペアを読み取り |

## テストカバレッジマトリックス

| テストクラス | ケース数 | カバレッジ対象 |
|--------|--------|---------|
| `TestSpliteUtils` | 14 | 接続・テーブル作成、正規化、挿入/読み取り、追加/重複排除、ページング検索、クリア、増分/グループ読み取り、状態遷移、event_id 移行、削除、ペア読み取り |

## 主要テストシナリオ

### テーブル作成とインデックス

- `connect_db` は `records` テーブルおよび `idx_records_event_id`、`idx_records_status_id` インデックスを自動作成
- `result_json` フィールドの存在を検証

### 正規化

- メタ情報行（`error_ts` なし）は `None` を返し、データベースに保存されない
- エラーレコードは `status="failed"` に正規化され、`task_json` と `result_json` は JSON 文字列にシリアライズされる

### 挿入と読み取り

- メタ情報行の挿入は `False` を返し、書き込まれない
- `load_records` は `status` でフィルタ可能

### 追加と重複排除

- `append_records` は既存の `event_id` をスキップし、繰り返し同期の冪等性を保証

### ページング検索

- `query_records` は `page`/`page_size`/`node`/`keyword`/`sort_order` パラメータをサポート
- ソートルール（newest/oldest）とフィルタ精度を検証

### 状態遷移

- `promote_record_to_failed_by_event_id`: waiting→failed、event_id とエラー情報を更新
- `promote_record_to_success_by_event_id`: pending→success、結果を書き込み
- `update_record_event_id_by_event_id`: 現在の状態を保持し、event_id のみ移行

### 増分とグループ化

- `get_max_event_id_in_fail` は failed 状態のみを集計
- `load_records_after_event_id_in_fail` は event_id 下限で増分読み取り
- `load_records_grouped_by_stage` は failed レコードのみを返し、stage 別にグループ化

### ペア読み取り

- `load_task_error_records` は `(task_json, (error_type, error_message))` リストを返し、stage フィルタをサポート
- `load_task_result_records` は `(task_json, result_json)` リストを返す

## 実行方法

```bash
# 全部执行
pytest tests/persistence/test_splite.py -v

# 按关键字匹配
pytest tests/persistence/test_splite.py -k "connect or normalize" -v
pytest tests/persistence/test_splite.py -k "insert or append" -v
pytest tests/persistence/test_splite.py -k "promote" -v
pytest tests/persistence/test_splite.py -k "group" -v
pytest tests/persistence/test_splite.py -k "load_task" -v
```

## 注意事項

- テストは `tmp_path` fixture を使用して一時 sqlite ファイルを作成し、テスト終了後に自動クリーンアップされます
- `sample_errors` fixture は 3 件の有効なエラーレコード + 1 件のメタ情報行をテストデータセットとして提供します
- 関連実装は `src/celestialflow/persistence/util_sqlite.py` にあります
