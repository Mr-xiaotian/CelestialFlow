# SQLite 工具测试 (test_splite.py)

> 📅 最后更新日期: 2026/07/16

## 作用

验证 `celestialflow.persistence.util_sqlite` 模块中所有 sqlite 工具函数，确保数据库建表、记录增删改查、状态迁移与按 stage 聚合等功能正确可靠。

## 核心测试对象

| 函数 | 说明 |
|------|------|
| `connect_db` | 建立连接并自动创建 records 表和索引 |
| `normalize_record` | 将错误记录归一化为 sqlite 可写格式 |
| `insert_record` | 单条插入记录（忽略元信息行） |
| `load_records` | 按状态过滤读取全部记录 |
| `append_records` | 批量追加记录（跳过重复 event_id） |
| `query_records` | 分页、筛选、排序查询 |
| `query_error_type_counts` | 按错误类型聚合 failed 记录数量，可按节点过滤 |
| `clear_records` | 清空 records 表 |
| `get_max_event_id_in_fail` | 仅统计 failed 状态的最大 event_id |
| `load_records_after_event_id_in_fail` | 按 failed event_id 下界增量读取 |
| `promote_record_to_failed_by_event_id` | 更新状态为 failed 并写入错误信息 |
| `promote_record_to_success_by_event_id` | 更新状态为 success 并写入结果 |
| `update_record_event_id_by_event_id` | 迁移记录的 event_id |
| `delete_record_by_event_id` | 按 event_id 删除记录 |
| `load_task_error_records` | 按 stage 读取 task-error 对 |
| `load_task_result_records` | 按 stage 读取 task-result 对 |

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestSpliteUtils` | 18 | 连接建表、归一化、插入/读取、追加/去重、分页查询、清空、增量和分组读取、错误类型聚合、状态迁移、event_id 迁移、删除、配对读取 |

## 关键测试场景

### 建表与索引

- `connect_db` 自动创建 `records` 表及 `idx_records_event_id`、`idx_records_status_id` 索引
- 验证 `result_json` 字段存在

### 归一化

- 元信息行（无 `ts`）返回 `None`，不存入数据库
- 错误记录被规范化为 `status="failed"`，`task_json` 和 `result_json` 序列化为 JSON 字符串

### 插入与读取

- 元信息行插入返回 `False`，不写入
- `load_records` 可按 `status` 过滤

### 追加与去重

- `append_records` 跳过已存在的 `event_id`，保证重复同步幂等

### 分页查询

- `query_records` 支持 `page`/`page_size`/`node`/`keyword`/`sort_order` 参数
- 验证排序规则（newest/oldest）和筛选准确性

### 错误类型聚合

- `query_error_type_counts` 按错误类型（`error_type`）聚合全部 failed 记录的数量
- `query_error_type_counts` 支持 `node` 参数按 stage 过滤
- 仅统计 status 为 `failed` 的记录，忽略 success 等其他状态

### 状态迁移

- `promote_record_to_failed_by_event_id`: 从 waiting→failed，更新 event_id 和错误信息
- `promote_record_to_success_by_event_id`: 从 pending→success，写入结果
- `update_record_event_id_by_event_id`: 保留当前状态，仅迁移 event_id

### 增量与分组

- `get_max_event_id_in_fail` 仅统计 failed 状态；无 failed 记录时返回 `None`
- `load_records_after_event_id_in_fail` 按 event_id 下界增量读取
- `load_task_error_records` 支持按 stage 过滤，返回 `(task_json, (error_type, error_message))` 列表

### 配对读取

- `load_task_error_records` 返回 `(task_json, (error_type, error_message))` 列表，支持按 stage 过滤
- `load_task_result_records` 返回 `(task_json, result_json)` 列表

## 运行方式

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

## 注意事项

- 测试使用 `tmp_path` fixture 创建临时 sqlite 文件，在测试结束后自动清理
- `sample_errors` fixture 提供 3 条有效错误记录 + 1 条元信息行作为测试数据集
- 相关实现位于 `src/celestialflow/persistence/util_sqlite.py`
