# PersistenceSQLite

> 📅 最后更新日期: 2026/07/16

`persistence/util_sqlite.py` 提供 SQLite 数据库的连接管理与记录 CRUD 操作工具，是 `FallbackSpout` 和 `TaskReporter` 的底层存储引擎。

## 核心函数概览

| 函数 | 说明 |
|------|------|
| `connect_db(db_path)` | 创建 SQLite 连接，配置 WAL 模式，确保表结构 |
| `insert_record(conn, record)` | 插入一条记录 |
| `promote_record_to_failed_by_event_id(...)` | 将 pending 记录晋升为 failed |
| `promote_record_to_success_by_event_id(...)` | 将 pending 记录晋升为 success |
| `update_record_event_id_by_event_id(...)` | 更新记录的 event_id |
| `delete_record_by_event_id(conn, event_id)` | 按 event_id 删除记录 |
| `load_records(db_path, status)` | 按状态加载记录 |
| `load_tasks_grouped_by_stage(db_path, statuses)` | 按 stage 分组加载 |
| `load_records_after_event_id_in_fail(db_path, min_event_id)` | 增量加载失败记录 |
| `query_records(db_path, page, page_size, ...)` | 分页条件查询 |
| `load_task_error_records(db_path, stage)` | 按 stage 加载 (task, error) 对 |
| `load_task_result_records(db_path, stage)` | 按 stage 加载 (task, result) 对 |

## 数据库表结构

```sql
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    ts REAL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    error_type TEXT NOT NULL DEFAULT '',
    error_message TEXT NOT NULL DEFAULT '',
    task_json TEXT NOT NULL,
    result_json TEXT NOT NULL DEFAULT 'null'
)
```

**索引：**
- `idx_records_event_id` (UNIQUE)：按 event_id 快速定位
- `idx_records_status_id`：按 (status, id) 组合查询

## 连接管理

### connect_db

```python
def connect_db(db_path: str | Path) -> sqlite3.Connection:
    """
    创建 sqlite 连接并交给调用方管理其生命周期。

    :param db_path: sqlite 数据库文件路径
    :return: 可直接用于记录读写的 sqlite 连接
    """
```

自动配置：
- `check_same_thread=False` — 多线程安全
- `journal_mode=WAL` — 写操作不阻塞读
- `synchronous=NORMAL` — 平衡性能与安全
- `foreign_keys=ON` — 启用外键约束

## 记录操作

### 写入操作（需传入 conn）

以下函数需要调用方自行管理 `conn` 的生命周期（通常由 `FallbackSpout` 持有）：

| 函数 | 签名要点 | 说明 |
|------|---------|------|
| `insert_record` | `(conn, record: dict) -> bool` | 归一化后 INSERT |
| `promote_record_to_failed_by_event_id` | `(conn, event_id, new_event_id, *, ts, error_type="", error_message="") -> bool` | 更新 event_id、status='failed' 和错误信息 |
| `promote_record_to_success_by_event_id` | `(conn, event_id, result, *, ts) -> bool` | 更新 status='success' + result_json |
| `update_record_event_id_by_event_id` | `(conn, old_event_id, new_event_id, *, ts) -> bool` | 更新 event_id（用于重试） |
| `delete_record_by_event_id` | `(conn, event_id) -> bool` | 删除记录 |

### 读取操作（自行管理连接）

以下函数内部自行 `connect_db` 并 `close`：

| 函数 | 签名要点 | 返回类型 |
|------|---------|---------|
| `load_records` | `(db_path, status="failed")` | `list[dict]` |
| `load_tasks_grouped_by_stage` | `(db_path, statuses=["failed"])` | `dict[str, list[dict]]` |
| `load_records_after_event_id_in_fail` | `(db_path, min_event_id)` | `list[dict]` |
| `query_records` | `(db_path, page, page_size, node, keyword, sort_order, status)` | `(total, total_pages, items)` |
| `load_task_error_records` | `(db_path, stage)` | `list[(task, (error_type, error_message))]` |
| `load_task_result_records` | `(db_path, stage)` | `list[(task, result)]` |

## 使用示例

### 基本读写操作

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

### 从 TaskExecutor 恢复失败任务

`TaskExecutor.start_db()` 内部调用 `load_tasks_grouped_by_stage`：

```python
from celestialflow.persistence.util_sqlite import load_tasks_grouped_by_stage

grouped = load_tasks_grouped_by_stage("fallback/2026-06-18/errors.sqlite3", ["failed"])
# {'StageA': [{'event_id': 1, 'task_json': 'hello', ...}, ...],
#  'StageB': [{'event_id': 2, 'task_json': 'world', ...}]}
```

### 分页查询错误记录

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

## 注意事项

- **写入函数**（insert/promote/update/delete）需要调用方传入 `conn` 并在操作后手动 `commit()`。
- **读取函数**（load/query）内部自行管理连接生命周期，调用方无需关心连接。
- `insert_record` 使用 `INSERT`，基于 `event_id` 唯一索引保证唯一性；外部批量写入时通常配合 `append_records` 捕获 `IntegrityError` 实现幂等。
- 归一化函数 `normalize_record` 会过滤掉缺少 `event_id` 的记录（返回 `None`）。
- `task_json` 和 `result_json` 存储的是 `json.dumps` 后的字符串，读取时通过 `json.loads` 还原。
