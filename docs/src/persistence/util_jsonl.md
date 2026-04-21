# PersistenceJSONL

`persistence/util_jsonl.py` 提供 JSONL 持久化与读取工具。

## 读取接口

- `load_jsonl_logs`：按行读取，可选字段过滤，支持从指定行号开始。
- `load_jsonl_grouped_by_keys`：按多个字段分组读取，支持字段提取和 `ast.literal_eval` 反序列化。
- `load_task_by_stage`：加载错误记录，按 stage 分类。
- `load_task_by_error`：加载错误记录，按 error 和 stage 分类。
