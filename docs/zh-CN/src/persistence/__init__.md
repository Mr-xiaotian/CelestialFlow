# Persistence 模块

> 📅 最后更新日期: 2026/08/12

Persistence 模块提供了 CelestialFlow 的数据持久化功能，包括执行日志记录和 fallback（回退）持久化。它确保任务执行的关键数据能够可靠地保存和检索。

## 导出符号

| 导出符号 | 来源模块 | 说明 |
|---------|---------|------|
| `FallbackInlet` | `core_fallback` | 线程安全的 fallback 记录收集器，通过队列将任务生命周期事件发送到 `FallbackSpout` |
| `FallbackSpout` | `core_fallback` | Fallback 记录监听器，将任务生命周期写入 SQLite 数据库 |
| `LogInlet` | `core_log` | 线程安全的日志收集器，提供丰富的语义化日志方法 |
| `LogSpout` | `core_log` | 日志监听线程，将日志写入 `logs/` 目录的文本文件 |
| `funnel_scope` | `core_scope` | 管理全局 FallbackSpout 与 LogSpout 生命周期的上下文管理器 |
| `get_fallback_inlet` | `core_fallback` | 获取全局唯一的 FallbackInlet 实例 |
| `get_fallback_spout` | `core_fallback` | 获取全局唯一的 FallbackSpout 实例 |
| `get_log_inlet` | `core_log` | 获取全局唯一的 LogInlet 实例 |
| `get_log_spout` | `core_log` | 获取全局唯一的 LogSpout 实例 |

## 文件说明

### 日志持久化

1. **core_log.py** (`LogSpout`, `LogInlet`)
   - **作用**: 日志记录和存储的基础架构
   - **核心组件**:
     - `LogSpout`: 日志监听线程，从队列接收日志消息并写入 `logs/` 目录下的文本文件
     - `LogInlet`: 线程安全日志收集器，提供语义化日志方法（任务成功/失败/重试、阶段启停、队列操作等）
   - **日志格式**: 纯文本格式，每行包含 `timestamp level message`

### Fallback 持久化

2. **core_fallback.py** (`FallbackSpout`, `FallbackInlet`)
   - **作用**: 任务生命周期的回退持久化，统一处理成功和失败结果
   - **核心组件**:
     - `FallbackSpout`: 继承 `BaseSpout`，通过 SQLite 持久化任务生命周期事件
     - `FallbackInlet`: 线程安全收集器，提供 `task_in`/`task_success`/`task_fail`/`task_retry`/`task_duplicate` 方法
   - **存储格式**: SQLite 数据库（WAL 模式）

### 作用域管理

3. **core_scope.py** (`funnel_scope`)
   - **作用**: 管理全局 FallbackSpout 与 LogSpout 生命周期的上下文管理器
   - **关键功能**: 进入时启动两个 spout，退出时停止并收集异常

### 数据序列化

4. **util_payload.py**
   - **作用**: 将任务数据递归转换为 JSON 友好的持久化结构
   - **关键函数**: `to_persisted_payload(task)` — 将任意 Python 对象转为可 JSON 序列化的结构

### SQLite 工具

5. **util_sqlite.py**
   - **作用**: SQLite 数据库的连接管理和 CRUD 操作工具
   - **关键函数**: `connect_db`、`insert_record`、`load_records`、`query_records`、`load_task_error_records` 等

## 模块关联

### 内部关联
- 所有持久化类都继承自 `BaseSpout`/`BaseInlet`（定义在 Funnel 模块）
- `FallbackSpout`/`FallbackInlet` 和 `LogSpout`/`LogInlet` 配对使用
- `FallbackSpout` 统一处理成功和失败结果，替代了旧版独立的 `SuccessSpout`

### 外部关联
- **与 Runtime 模块**: 监听运行时产生的日志和错误，引用 `LEVEL_DICT`
- **与 Stage 模块**: 记录任务执行状态和结果
- **与 Observability 模块**: 提供原始数据用于监控和分析
- **与 Funnel 模块**: 继承 `BaseSpout`/`BaseInlet` 基类

## 架构特点

### 异步非阻塞设计
- Spout 在后台线程运行，不阻塞主流程
- Inlet 通过队列发送数据，非阻塞写入

### 生产者-消费者模式

```mermaid
flowchart LR
    subgraph Producer[生产者 - Worker 线程]
        LogInlet[LogInlet]
        FallbackInlet[FallbackInlet]
    end

    LogInlet -->|_log -> _funnel| LogQueue[日志队列<br/>queue.Queue]
    FallbackInlet -->|task_in / task_success / task_fail 等| FallbackQueue[Fallback 队列<br/>queue.Queue]

    LogQueue -->|守护线程轮询| LogSpout[LogSpout]
    FallbackQueue -->|守护线程轮询| FallbackSpout[FallbackSpout]

    LogSpout -->|_handle_record| LogFile[logs/*.log]
    FallbackSpout -->|SQLite 操作| SQLiteFile[fallback/**/*.sqlite3]
```

### 文件名规范

| 持久化类型 | 文件路径模式 |
|-----------|-------------|
| 日志 | `logs/task_logger({日期}).log` |
| Fallback | `fallback/{日期}/{来源}({时间}).sqlite3` |

## 使用示例

### 基础配置

```python
from celestialflow.persistence import funnel_scope

# 使用 funnel_scope 统一管理生命周期
with funnel_scope():
    # FallbackSpout 和 LogSpout 已自动启动
    # 执行业务逻辑...
    ...
# 退出作用域时两个 Spout 已自动停止
```

### 记录日志

```python
# 记录执行器启停
log_inlet.start_executor("StageA", 100, "thread")
log_inlet.end_executor("StageA", "thread", 12.5, 98, 2, 0)

# 记录任务生命周期
log_inlet.task_success("func", "task1", "thread", "result", 0.05, 1, 2)
log_inlet.task_fail("func", "task2", ValueError("bad"), 3, 4)
```

### 记录 fallback

```python
# 任务进入
fallback_inlet.task_in("StageA", event_id=1, task="hello")

# 任务成功
fallback_inlet.task_success(event_id=1, result="OK", persist=True)

# 任务失败
fallback_inlet.task_fail(event_id=2, error_id=10, error=ValueError("bad"))
```

### 读取持久化数据

```python
from celestialflow.persistence.util_sqlite import load_records, load_task_error_records

# 读取失败记录
errors = load_task_error_records("fallback/2026-06-18/errors.sqlite3", "StageA")
for task, (error_type, error_msg) in errors:
    print(f"{task}: {error_type} - {error_msg}")
```
