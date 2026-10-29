# tests/persist/test_sqlite.py

> 📅 最后更新日期: 2026/10/30

## 作用

验证 `celestialflow.persist.util_sqlite` 中的 sqlite 工具函数，确保建表与索引、记录归一化、单条插入、状态迁移（failed / success）、重试信息更新、按 event_id 删除以及按节点配对读取等功能正确可靠。

> 该测试文件由历史遗留的 `test_splite.py` 更名而来，测试类名 `TestSpliteUtils` 沿用历史拼写（应为 `TestSqliteUtils`），此处按源码保留。

## 核心测试对象

被测函数全部来自 `celestialflow.persist.util_sqlite`：

| 函数 | 说明 |
|------|------|
| `connect_db` | 建立连接（`check_same_thread=False`、WAL、`synchronous=NORMAL`），自动创建 records 表与索引，旧库缺列时自动补 `retry_times` |
| `normalize_record` | 将记录归一化为 sqlite 可写格式；无 `event_id` 的元信息行返回 `None`，业务记录缺少 `node` 或 `status` 时抛出 `KeyError` |
| `insert_record` | 在已有连接上插入单条记录，元信息行返回 `False`，实际插入返回 `True` |
| `row_to_record_dict` | 将 `sqlite3.Row` 转为对外记录字典，并把 `task_json` / `result_json` 反序列化为 Python 对象 |
| `promote_record_to_failed_by_event_id` | 更新状态为 failed、把 `event_id` 替换为错误事件 ID，并写入错误信息与时间戳 |
| `promote_record_to_success_by_event_id` | 更新状态为 success、写入结果与时间戳，保留原 `event_id` |
| `update_retry_by_event_id` | 更新记录的重试次数与最近一次错误信息，状态保持不变；记录不存在时返回 `False` |
| `delete_record_by_event_id` | 按 event_id 删除记录 |
| `load_task_error_records` | 按节点读取 `(task_json, (error_type, error_message))` 列表 |
| `load_task_result_records` | 按节点读取 `(task_json, result_json)` 列表 |

本文件另定义两个测试辅助函数（非被测对象）：

| 辅助函数 | 说明 |
|----------|------|
| `_insert_records(sqlite_path, records)` | 用 `connect_db` + `insert_record` 逐条写入，遇 `sqlite3.IntegrityError`（重复 `event_id`）跳过，返回实际写入条数 |
| `_fetch_records(sqlite_path, status)` | 用 `connect_db` 按 `status` 查询并用 `row_to_record_dict` 转成字典列表，供断言读取 |

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestSpliteUtils` | 11 | 连接建表与索引、归一化、插入与读取、failed / success 状态迁移、重试更新（含记录缺失）、按 event_id 删除、按节点配对读取 |

## 关键测试场景

### 建表与索引

- `connect_db` 自动创建 `records` 表、`idx_records_event_id`（唯一）与 `idx_records_status_id` 索引。
- 通过 `PRAGMA index_list(records)` 确认 `idx_records_event_id` 为唯一索引。
- 核对表结构字段顺序为 `id / event_id / ts / node / status / error_type / error_message / task_json / result_json / retry_times`，并确认 `result_json` 字段存在。

### 归一化

- 缺少 `event_id` 的元信息行（如仅含 `timestamp` / `graph_name`）`normalize_record` 返回 `None`。
- 业务记录缺少 `node` 或 `status` 时抛出 `KeyError`，匹配消息中的字段名。
- 有效记录被规范化为 `event_id` / `node` / `status` / `error_type` / `error_message` / `ts` / `retry_times` 等字段，`retry_times` 默认为 0，`task_json` 序列化为 JSON 字符串。

### 插入与读取

- 元信息行 `insert_record` 返回 `False` 且不写入；两条有效记录返回 `True`。
- `_fetch_records` 经 `row_to_record_dict` 读回时 `task_json` 被反序列化为 Python 对象、`result_json` 为 `None`，且 `id` 按插入顺序自增。

### 状态迁移

- `promote_record_to_failed_by_event_id`: 从 waiting 记录（`event_id=9`）迁移到新错误事件 ID（19），写入 `status="failed"`、`ts=9.5`、`error_type="RuntimeError"`、`error_message="boom"`，返回 `True`。
- `promote_record_to_success_by_event_id`: 从 pending 记录（`event_id=8`）晋升为 success，保留原 `event_id`，写入 `ts=8.5` 与 `result_json`，`task_json` 保持不变。

### 重试更新

- `update_retry_by_event_id`: 对 pending 记录写入 `retry_times=2`、`ts`、`error_type` / `error_message`，状态仍为 `pending`，返回 `True`。
- 对不存在的 `event_id=999` 更新返回 `False`。

### 删除

- `delete_record_by_event_id(conn, 2)` 返回 `True`，剩余 failed 记录的 `event_id` 为 `[1, 3]`。

### 配对读取

- `load_task_error_records(db_path, "s1")` 只返回 s1 的 failed 记录，按 `id` 升序，元素为 `(task_json, (error_type, error_message))`。
- `load_task_result_records(db_path, "s8")` 返回 `[(task_json, result_json)]`。

## 运行方式

```bash
# 全部执行
pytest tests/persist/test_sqlite.py -v

# 按关键字匹配
pytest tests/persist/test_sqlite.py -k "connect or normalize" -v
pytest tests/persist/test_sqlite.py -k "insert" -v
pytest tests/persist/test_sqlite.py -k "promote or retry" -v
pytest tests/persist/test_sqlite.py -k "delete" -v
pytest tests/persist/test_sqlite.py -k "load_task" -v
```

## 注意事项

- 测试使用 `tmp_path` fixture 创建临时 sqlite 文件，在测试结束后自动清理。
- `sample_errors` fixture 提供 3 条有效错误记录 + 1 条元信息行作为测试数据集；`sqlite_path` fixture 提供 `tmp_path / "records.sqlite3"` 路径。
- 所有写操作都在 `connect_db` 返回的连接上执行，由测试自行 `commit()` 并 `close()`。
- sqlite `records` 表中的节点标识字段为 `node`，所有按节点读取 / 过滤的函数均以 `node` 为准。
- 相关实现位于 `src/celestialflow/persist/util_sqlite.py`。
