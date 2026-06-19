# PersistenceSQLite

> 📅 最終更新日: 2026/06/18

`persistence/util_sqlite.py` は、SQLite データベースの接続管理とレコード CRUD 操作ツールを提供し、`FallbackSpout` および `TaskReporter` の基盤ストレージエンジンです。

## コア関数概要

| 関数 | 説明 |
|------|------|
| `connect_db(db_path)` | SQLite 接続を作成し、WAL モードを設定、テーブル構造を確保 |
| `insert_record(conn, record)` | レコードを1件挿入 |
| `promote_record_to_failed_by_event_id(...)` | pending レコードを failed に昇格 |
| `promote_record_to_success_by_event_id(...)` | pending レコードを success に昇格 |
| `update_record_event_id_by_event_id(...)` | レコードの event_id を更新 |
| `delete_record_by_event_id(conn, event_id)` | event_id でレコードを削除 |
| `load_records(db_path, status)` | ステータスでレコードを読み込み |
| `load_records_grouped_by_stage(db_path, status)` | stage 別にグループ化して読み込み |
| `load_records_after_event_id_in_fail(db_path, min_event_id)` | 失敗レコードを増分読み込み |
| `query_records(db_path, page, page_size, ...)` | ページング条件検索 |
| `load_task_error_records(db_path, stage)` | stage 別に (task, error) ペアを読み込み |
| `load_task_result_records(db_path, stage)` | stage 別に (task, result) ペアを読み込み |

## データベーステーブル構造

```sql
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    stage TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'failed',
    error_type TEXT NOT NULL DEFAULT '',
    error_message TEXT NOT NULL DEFAULT '',
    ts REAL,
    task_json TEXT NOT NULL DEFAULT 'null',
    result_json TEXT NOT NULL DEFAULT 'null'
)
```

**インデックス：**
- `idx_records_event_id` (UNIQUE)：event_id で高速検索
- `idx_records_status_id`：(status, id) の組み合わせ検索

## 接続管理

### connect_db

```python
def connect_db(db_path: str | Path) -> sqlite3.Connection:
    """
    创建 sqlite 连接并交给调用方管理其生命周期。

    :param db_path: sqlite 数据库文件路径
    :return: 可直接用于记录读写的 sqlite 连接
    """
```

自動設定：
- `check_same_thread=False` — マルチスレッド安全
- `journal_mode=WAL` — 書き込み操作が読み取りをブロックしない
- `synchronous=NORMAL` — パフォーマンスと安全性のバランス
- `foreign_keys=ON` — 外部キー制約を有効化

## レコード操作

### 書き込み操作（conn を渡す必要あり）

以下の関数は呼び出し側で `conn` のライフサイクルを管理する必要があります（通常は `FallbackSpout` が保持）：

| 関数 | シグネチャ要点 | 説明 |
|------|---------|------|
| `insert_record` | `(conn, record: dict) -> bool` | 正規化後に INSERT OR REPLACE |
| `promote_record_to_failed_by_event_id` | `(conn, event_id, error_id, ts, error_type, error_message) -> bool` | status + エラー情報を更新 |
| `promote_record_to_success_by_event_id` | `(conn, event_id, result) -> bool` | status='success' + result_json を更新 |
| `update_record_event_id_by_event_id` | `(conn, old_event_id, new_event_id) -> bool` | event_id を更新（リトライ用） |
| `delete_record_by_event_id` | `(conn, event_id) -> bool` | レコードを削除 |

### 読み取り操作（接続を自己管理）

以下の関数は内部で `connect_db` と `close` を自己管理します：

| 関数 | シグネチャ要点 | 戻り値の型 |
|------|---------|---------|
| `load_records` | `(db_path, status="failed")` | `list[dict]` |
| `load_records_grouped_by_stage` | `(db_path, status="failed")` | `dict[str, list[dict]]` |
| `load_records_after_event_id_in_fail` | `(db_path, min_event_id)` | `list[dict]` |
| `query_records` | `(db_path, page, page_size, node, keyword, sort_order, status)` | `(total, total_pages, items)` |
| `load_task_error_records` | `(db_path, stage)` | `list[(task, (error_type, error_message))]` |
| `load_task_result_records` | `(db_path, stage)` | `list[(task, result)]` |

## 使用例

### 基本的な読み書き操作

```python
import sqlite3
from pathlib import Path
from celestialflow.persistence.util_sqlite import (
    connect_db,
    insert_record,
    load_records,
    delete_record_by_event_id,
)

# 1. 创建连接
conn = connect_db("test_data.sqlite3")

# 2. 写入记录
record = {
    "event_id": 1,
    "stage": "StageA",
    "status": "pending",
    "task_json": "hello world",
}
insert_record(conn, record)
conn.commit()
conn.close()

# 3. 读取记录（自动管理连接）
records = load_records("test_data.sqlite3", status="pending")
for r in records:
    print(f"event_id={r['event_id']}, task={r['task_json']}")

# 4. 清理
Path("test_data.sqlite3").unlink()
```

### TaskExecutor からの失敗タスク復旧

`TaskExecutor.start_db()` は内部で `load_records_grouped_by_stage` を呼び出します：

```python
from celestialflow.persistence.util_sqlite import load_records_grouped_by_stage

grouped = load_records_grouped_by_stage("fallback/2026-06-18/errors.sqlite3", "failed")
# {'StageA': [{'event_id': 1, 'task_json': 'hello', ...}, ...],
#  'StageB': [{'event_id': 2, 'task_json': 'world', ...}]}
```

### エラーレコードのページング検索

```python
from celestialflow.persistence.util_sqlite import query_records

total, total_pages, items = query_records(
    db_path="fallback/2026-06-18/errors.sqlite3",
    page=1,
    page_size=20,
    node="",
    keyword="ValueError",
    sort_order="newest",
    status="failed",
)
print(f"共 {total} 条，第 1/{total_pages} 页")
for item in items:
    print(f"  [{item['event_id']}] {item['error_type']}: {item['error_message']}")
```

## 注意事項

- **書き込み関数**（insert/promote/update/delete）は呼び出し側で `conn` を渡し、操作後に手動で `commit()` する必要があります。
- **読み取り関数**（load/query）は内部で接続ライフサイクルを自己管理するため、呼び出し側は接続を気にする必要がありません。
- `insert_record` は `INSERT OR REPLACE` を使用し、`event_id` のユニークインデックスに基づいて upsert を行います。
- 正規化関数 `normalize_record` は `event_id` がないレコードをフィルタリングします（`None` を返します）。
- `task_json` と `result_json` には `json.dumps` 後の文字列が格納され、読み取り時に `json.loads` で復元されます。
