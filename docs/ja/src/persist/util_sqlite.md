# src/celestialflow/persist/util_sqlite.py

> 📅 最終更新日: 2026/10/09

`persist/util_sqlite.py` は、SQLite データベースの接続管理とレコード CRUD 操作ツールを提供し、`LifecycleSpout` の基盤となるストレージエンジンです。

## コア関数概要

| 関数 | 説明 |
|------|------|
| `connect_db(db_path)` | SQLite 接続を作成し、WAL モードを設定、テーブル構造とインデックスを確保 |
| `normalize_record(record)` | レコードを sqlite 書き込み可能な形式に正規化（`event_id` がない場合は `None` を返す） |
| `row_to_record_dict(row)` | sqlite の行を対外的なレコード辞書に変換 |
| `insert_record(conn, record)` | レコードを 1 件挿入 |
| `promote_record_to_success_by_event_id(...)` | レコードを success に昇格し、結果を書き込む |
| `promote_record_to_skipped_by_event_id(...)` | レコードを skipped に昇格し、新しいイベント ID に切り替える |
| `promote_record_to_failed_by_event_id(...)` | レコードを failed に昇格し、新しいイベント ID に切り替える |
| `update_retry_by_event_id(conn, event_id, *, ts, retry_times, ...)` | pending レコードのリトライ回数と直近のエラー情報を更新 |
| `delete_record_by_event_id(conn, event_id)` | event_id でレコードを削除 |
| `clear_records(db_path)` | データベース内の全レコードをクリア |
| `append_records(db_path, records)` | バッチ追加書き込み。event_id 衝突時はスキップ（冪等） |
| `get_max_event_id_in_fail(db_path)` | 失敗レコード内の最大 event_id を読み込み |
| `load_records(db_path, status)` | ステータスでレコードを読み込み |
| `load_tasks_grouped_by_node(db_path, statuses)` | node 別にグループ化して読み込み |
| `load_records_after_event_id_in_fail(db_path, min_event_id)` | 失敗レコードの増分読み込み |
| `query_records(db_path, page, page_size, ...)` | ページング条件検索 |
| `query_error_type_counts(db_path, node, status)` | エラータイプ別に集計 |
| `load_task_error_records(db_path, node)` | node 別に (task, error) ペアを読み込み |
| `load_task_result_records(db_path, node)` | node 別に (task, result) ペアを読み込み |

## データベーステーブル構造

```sql
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    ts REAL,
    node TEXT NOT NULL,
    status TEXT NOT NULL,
    error_type TEXT NOT NULL DEFAULT '',
    error_message TEXT NOT NULL DEFAULT '',
    task_json TEXT NOT NULL,
    result_json TEXT NOT NULL DEFAULT 'null',
    retry_times INTEGER NOT NULL DEFAULT 0
)
```

> 旧データベースとの互換性：`_ensure_table` は `retry_times` 列をチェックし、欠落している場合は自動的に `ALTER TABLE` で補完します。

**インデックス：**
- `idx_records_event_id` (UNIQUE)：event_id で高速検索
- `idx_records_status_id`：(status, id) の組み合わせ検索

> テーブル内の `node` フィールドはタスクが属するノードを識別します（ビジネスフィールドであり、呼び出し側が明示的に書き込む必要があります）。

## 接続管理

### connect_db

```python
def connect_db(db_path: str | Path) -> sqlite3.Connection:
```

自動設定：
- `check_same_thread=False` — マルチスレッド安全
- `journal_mode=WAL` — 書き込み操作が読み取りをブロックしない
- `synchronous=NORMAL` — パフォーマンスと安全性のバランス
- `foreign_keys=ON` — 外部キー制約を有効化

同時にテーブル構造とインデックスの存在を確保します。

## レコードのシリアライズ

### normalize_record

```python
def normalize_record(record: dict[str, Any]) -> dict[str, Any] | None:
```

- `event_id` がない場合は `None` を返します（ビジネスレコードではないものは無視されます）。
- ビジネスレコードは `node` と `status` を明示的に提供する必要があります。
- 出力は標準パラメータ辞書：`event_id` / `node` / `status` / `error_type` / `error_message` / `ts` / `task_json` / `result_json` / `retry_times`。`task_json` / `result_json` は `json.dumps(..., ensure_ascii=False)` の結果です。

### row_to_record_dict

sqlite の行（`sqlite3.Row`）を対外的なレコード辞書に変換します。`task_json` / `result_json` は `json.loads` で復元されます。

## レコード操作

### 書き込み操作（conn を渡す必要あり）

以下の関数は呼び出し側で `conn` のライフサイクルを管理する必要があります（通常は `LifecycleSpout` が保持）レコード変更後、手動で `commit()` します：

| 関数 | シグネチャ要点 | 説明 |
|------|---------|------|
| `insert_record` | `(conn, record: dict) -> bool` | 正規化後に INSERT |
| `update_retry_by_event_id` | `(conn, event_id, *, ts, retry_times, error_type="", error_message="") -> bool` | pending 状態を保ち、リトライ回数と直近のエラー情報を更新 |
| `promote_record_to_success_by_event_id` | `(conn, event_id, result, *, ts) -> bool` | status='success' + result_json を更新 |
| `promote_record_to_skipped_by_event_id` | `(conn, event_id, new_event_id, *, ts) -> bool` | event_id、status='skipped' を更新 |
| `promote_record_to_failed_by_event_id` | `(conn, event_id, new_event_id, *, ts, error_type="", error_message="") -> bool` | event_id、status='failed' とエラー情報を更新 |
| `delete_record_by_event_id` | `(conn, event_id) -> bool` | レコードを削除 |

### 接続を自己管理する操作

以下の関数は内部で `connect_db` と `close` を自己管理します：

| 関数 | シグネチャ要点 | 戻り値の型 |
|------|---------|---------|
| `clear_records` | `(db_path)` | `None` |
| `append_records` | `(db_path, records)` | `int`（実際の増加数） |
| `get_max_event_id_in_fail` | `(db_path)` | `int | None` |
| `load_records` | `(db_path, status="failed")` | `list[dict]` |
| `load_tasks_grouped_by_node` | `(db_path, statuses=("failed", "pending"))` | `dict[str, list[dict]]` |
| `load_records_after_event_id_in_fail` | `(db_path, min_event_id)` | `list[dict]` |
| `query_records` | `(db_path, page, page_size, node, keyword, sort_order, status="failed")` | `(total, total_pages, items)` |
| `query_error_type_counts` | `(db_path, node="", status="failed")` | `list[dict]` |
| `load_task_error_records` | `(db_path, node)` | `list[(task, (error_type, error_message))]` |
| `load_task_result_records` | `(db_path, node)` | `list[(task, result)]` |

## 使用例

### 基本的な読み書き操作

```python
import sqlite3
from celestialflow.persist.util_sqlite import connect_db, insert_record, load_records

# 1. 接続を作成（自動設定 + テーブル作成）
conn = connect_db("test_data.sqlite3")

# 2. レコードを書き込み（conn を渡す）
record = {
    "event_id": 1,
    "node": "StageA",
    "status": "pending",
    "task_json": "hello world",
}
insert_record(conn, record)
conn.commit()
conn.close()

# 3. レコードを読み込み（接続を自動管理）
records = load_records("test_data.sqlite3", status="pending")
for r in records:
    print(f"event_id={r['event_id']}, node={r['node']}, task={r['task_json']}")
```

### node 別にグループ化して読み込み

```python
from celestialflow.persist.util_sqlite import load_tasks_grouped_by_node

grouped = load_tasks_grouped_by_node(
    "lifecycles/2026-10-09/flow_lifecycle(10-00-00-123).sqlite3",
    ("failed", "pending"),
)
```

`{node_name: [{"task_json": task, "error_type": str, "status": str}, ...]}` を返します。

### エラーレコードのページング検索

```python
from celestialflow.persist.util_sqlite import query_records

total, total_pages, items = query_records(
    db_path="lifecycles/2026-10-09/flow_lifecycle(10-00-00-123).sqlite3",
    page=1,
    page_size=20,
    node="",
    keyword="ValueError",
    sort_order="newest",
    status="failed",
)
print(f"全 {total} 件、第 1/{total_pages} ページ")
```

### タスクエラー / 結果ペアの読み込み

```python
from celestialflow.persist.util_sqlite import (
    load_task_error_records,
    load_task_result_records,
)

errors = load_task_error_records(
    db_path, node="StageA"
)  # [(task, (error_type, error_message))]
results = load_task_result_records(db_path, node="StageA")  # [(task, result)]
```

## 注意事項

- **書き込み関数**（insert/promote/delete）は呼び出し側で `conn` を渡し、操作後に手動で `commit()` する必要があります。`clear_records` / `append_records` とすべての読み取り関数は、内部で接続を自己管理します。
- `insert_record` は `INSERT` を使用し、`event_id` のユニークインデックスに基づいて一意性を保証します。外部からの一括書き込み時には通常 `append_records` と組み合わせて `IntegrityError` を捕捉し、冪等性を実現します。
- 正規化関数 `normalize_record` は `event_id` がないレコードをフィルタリングします（`None` を返します）。
- `task_json` と `result_json` には `json.dumps` 後の文字列が格納され、読み取り時に `json.loads` で復元されます。
- `retry_times` は `update_retry_by_event_id` によって維持され、タスクが昇格する前のリトライ回数を記録するために使用されます。
- **ビジネスフィールドの明示的な書き込み**：`node` と `status` はビジネスフィールドであり、レコード書き込み時に呼び出し側（`LifecycleInlet` など）が明示的に提供する必要があります。`normalize_record` はデフォルトの推定を行いません。