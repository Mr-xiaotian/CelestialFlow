# PersistenceJSONL

`persistence/jsonl.py` 提供 JSONL 持久化与读取工具。

## 写入接口

- `append_jsonl_log`：追加单条记录。
- `append_jsonl_logs`：批量追加记录。

## 读取接口

- `load_jsonl_logs`：按行读取，可选字段过滤。
- `load_jsonl_grouped_by_keys`：按字段分组读取。
- `load_task_by_stage` / `load_task_by_error`：错误任务聚合读取。
