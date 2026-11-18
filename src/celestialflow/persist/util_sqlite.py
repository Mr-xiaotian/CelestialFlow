# persist/util_sqlite.py
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

# ==== 连接与表结构 ====


def connect_db(db_path: str | Path) -> sqlite3.Connection:
    """
    创建 sqlite 连接并交给调用方管理其生命周期。

    :param db_path: sqlite 数据库文件路径
    :return: 可直接用于记录读写的 sqlite 连接
    :rtype: sqlite3.Connection
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        path, check_same_thread=False
    )  # 允许跨线程使用；使用端 spout 仅有单个消费线程，这里并发写入是安全的
    conn.row_factory = sqlite3.Row

    # 初始化当前连接的 sqlite 运行参数，再确保表结构与索引存在。
    _ = conn.execute("PRAGMA journal_mode=WAL")
    _ = conn.execute("PRAGMA synchronous=NORMAL")
    _ = conn.execute("PRAGMA foreign_keys=ON")
    _ensure_table(conn)
    return conn


def _ensure_table(conn: sqlite3.Connection) -> None:
    """
    在给定连接上确保状态表、事件表与索引存在。

    :param conn: 已建立的 sqlite 连接
    :return: None
    """
    table_names = {
        str(row["name"])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "records" in table_names and "status" not in table_names:
        _ = conn.execute("ALTER TABLE records RENAME TO status")

    # 当前状态快照表：供 restore_db 与结果查询使用。
    _ = conn.execute(
        """
        CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_event_id INTEGER NOT NULL,
            current_event_id INTEGER NOT NULL,
            ts REAL,
            node TEXT NOT NULL,
            status TEXT NOT NULL,
            error_type TEXT NOT NULL DEFAULT '',
            error_message TEXT NOT NULL DEFAULT '',
            task_json TEXT NOT NULL,
            result_json TEXT NOT NULL DEFAULT 'null',
            retry_times INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    # 不可变事件账本：保存全部生命周期事件本身。
    _ = conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY,
            event_type TEXT NOT NULL,
            node TEXT NOT NULL,
            ts REAL NOT NULL
        )
        """
    )
    # 事件父边表：保存事件间的因果关系。
    _ = conn.execute(
        """
        CREATE TABLE IF NOT EXISTS event_parents (
            event_id INTEGER NOT NULL,
            parent_id INTEGER NOT NULL,
            PRIMARY KEY (event_id, parent_id),
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES events(event_id) ON DELETE CASCADE
        )
        """
    )
    # 兼容旧库：为缺少 retry_times 列的历史表补充默认列。
    columns = {
        str(row["name"])
        for row in conn.execute("PRAGMA table_info(status)").fetchall()
    }
    if "input_event_id" not in columns:
        _ = conn.execute("ALTER TABLE status ADD COLUMN input_event_id INTEGER")
    if "current_event_id" not in columns:
        _ = conn.execute("ALTER TABLE status ADD COLUMN current_event_id INTEGER")
    if "retry_times" not in columns:
        _ = conn.execute(
            "ALTER TABLE status ADD COLUMN retry_times INTEGER NOT NULL DEFAULT 0"
        )
    columns = {
        str(row["name"])
        for row in conn.execute("PRAGMA table_info(status)").fetchall()
    }
    if "event_id" in columns:
        _ = conn.execute(
            """
            UPDATE status
            SET input_event_id = COALESCE(input_event_id, event_id),
                current_event_id = COALESCE(current_event_id, event_id)
            """
        )
    # 为常用查询条件建立索引，减少筛选和排序开销。
    _ = conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_status_input_event_id ON status(input_event_id)"
    )
    _ = conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_status_current_event_id ON status(current_event_id)"
    )
    _ = conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_status_status_id ON status(status, id)"
    )
    _ = conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_events_type_ts ON events(event_type, ts)"
    )
    _ = conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_events_node_ts ON events(node, ts)"
    )
    _ = conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_event_parents_parent_id ON event_parents(parent_id)"
    )
    conn.commit()


# ==== 记录序列化工具 ====


def normalize_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """
    将状态快照归一化为 sqlite 可写格式。

    非业务记录会返回 ``None``。业务记录必须显式提供 ``node`` 与
    ``status``。``input_event_id`` 缺失时会兼容读取旧字段 ``event_id``；
    ``current_event_id`` 缺失时默认与 ``input_event_id`` 相同。

    :param record: 原始状态字典
    :return: 可直接写入 sqlite 的参数字典，或 ``None``
    :rtype: dict[str, Any] | None
    """
    input_event_id = record.get("input_event_id", record.get("event_id"))
    if input_event_id is None:
        return None
    current_event_id = record.get("current_event_id", input_event_id)

    return {
        "input_event_id": int(input_event_id),
        "current_event_id": int(current_event_id),
        "node": str(record["node"]),
        "status": str(record["status"]),
        "error_type": str(record.get("error_type", "") or ""),
        "error_message": str(record.get("error_message", "") or ""),
        "ts": float(record.get("ts", 0.0) or 0.0),
        "task_json": json.dumps(record["task_json"], ensure_ascii=False),
        "result_json": json.dumps(record.get("result_json"), ensure_ascii=False),
        "retry_times": int(record.get("retry_times", 0) or 0),
    }


def row_to_record_dict(row: sqlite3.Row) -> dict[str, Any]:
    """
    将 sqlite 状态行转换为对外字典。

    :param row: sqlite 查询结果中的单行
    :return: 面向上层调用方的记录字典
    :rtype: dict[str, Any]
    """
    return {
        "id": int(row["id"]),
        "input_event_id": int(row["input_event_id"]),
        "current_event_id": int(row["current_event_id"]),
        "ts": float(row["ts"]),
        "node": str(row["node"]),
        "status": str(row["status"]),
        "error_type": str(row["error_type"]),
        "error_message": str(row["error_message"]),
        "task_json": json.loads(str(row["task_json"])),
        "result_json": json.loads(str(row["result_json"])),
        "retry_times": int(row["retry_times"]),
    }


def normalize_event_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """
    将事件记录归一化为 sqlite 可写格式。

    非业务记录会返回 ``None``。业务记录必须显式提供 ``event_type`` 与 ``node``。

    :param record: 原始事件记录字典
    :return: 可直接写入 sqlite 的参数字典，或 ``None``
    :rtype: dict[str, Any] | None
    """
    event_id = record.get("event_id")
    if event_id is None:
        return None

    return {
        "event_id": int(event_id),
        "event_type": str(record["event_type"]),
        "node": str(record["node"]),
        "ts": float(record.get("ts", 0.0) or 0.0),
    }


def row_to_event_dict(row: sqlite3.Row) -> dict[str, Any]:
    """
    将 sqlite 事件行转换为对外事件字典。

    :param row: sqlite 查询结果中的事件行
    :return: 面向上层调用方的事件字典
    :rtype: dict[str, Any]
    """
    return {
        "event_id": int(row["event_id"]),
        "event_type": str(row["event_type"]),
        "node": str(row["node"]),
        "ts": float(row["ts"]),
    }


# ==== 复用已有连接的写操作 ====


def insert_record(conn: sqlite3.Connection, record: dict[str, Any]) -> bool:
    """
    在给定连接上插入单条状态快照。

    元信息记录会被忽略。

    :param conn: 已建立的 sqlite 连接
    :param record: 原始状态字典
    :return: 是否实际插入了一条状态
    :rtype: bool
    """
    normalized = normalize_record(record)
    if normalized is None:
        return False

    # 插入单条归一化后的记录。
    _ = conn.execute(
        """
        INSERT INTO status (
            input_event_id, current_event_id, ts, node, status, error_type, error_message,
            task_json, result_json, retry_times
        )
        VALUES (
            :input_event_id, :current_event_id, :ts, :node, :status, :error_type,
            :error_message, :task_json, :result_json, :retry_times
        )
        """,
        normalized,
    )
    return True


def insert_event(conn: sqlite3.Connection, event: dict[str, Any]) -> bool:
    """
    在给定连接上插入单条生命周期事件。

    非业务记录会被忽略。

    :param conn: 已建立的 sqlite 连接
    :param event: 原始事件记录字典
    :return: 是否实际插入了一条事件
    :rtype: bool
    """
    normalized = normalize_event_record(event)
    if normalized is None:
        return False

    _ = conn.execute(
        """
        INSERT INTO events (event_id, event_type, node, ts)
        VALUES (:event_id, :event_type, :node, :ts)
        """,
        normalized,
    )
    return True


def insert_event_parents(
    conn: sqlite3.Connection,
    event_id: int,
    parent_ids: Iterable[int],
) -> int:
    """
    在给定连接上写入一条事件的全部父边。

    :param conn: 已建立的 sqlite 连接
    :param event_id: 子事件 ID
    :param parent_ids: 父事件 ID 列表
    仅为数据库中已存在的父事件写边，缺失父事件会被跳过。

    :return: 实际插入的父边数量
    :rtype: int
    """
    inserted = 0
    for parent_id in parent_ids:
        exists = conn.execute(
            """
            SELECT 1
            FROM events
            WHERE event_id = ?
            """,
            [int(parent_id)],
        ).fetchone()
        if exists is None:
            continue
        _ = conn.execute(
            """
            INSERT INTO event_parents (event_id, parent_id)
            VALUES (?, ?)
            """,
            [int(event_id), int(parent_id)],
        )
        inserted += 1
    return inserted


def promote_record_to_failed_by_input_event_id(
    conn: sqlite3.Connection,
    input_event_id: int,
    current_event_id: int,
    *,
    ts: float,
    error_type: str = "",
    error_message: str = "",
) -> bool:
    """
    在给定连接上按 ``input_event_id`` 将状态晋升为 failed，并推进当前事件指针。

    :param conn: 已建立的 sqlite 连接
    :param input_event_id: 任务输入事件 ID
    :param current_event_id: 当前状态对应的事件 ID
    :param ts: 生命周期更新时间戳
    :param error_type: 错误类型，默认空字符串
    :param error_message: 错误消息，默认空字符串
    :return: 是否更新到记录
    :rtype: bool
    """
    cursor = conn.execute(
        """
        UPDATE status
        SET current_event_id = ?, ts = ?, status = 'failed', error_type = ?, error_message = ?
        WHERE input_event_id = ?
        """,
        [int(current_event_id), ts, error_type, error_message, int(input_event_id)],
    )
    return cursor.rowcount > 0


def promote_record_to_success_by_input_event_id(
    conn: sqlite3.Connection,
    input_event_id: int,
    current_event_id: int,
    result: Any,
    *,
    ts: float,
) -> bool:
    """
    在给定连接上按 ``input_event_id`` 将状态晋升为 success，并写入结果。

    :param conn: 已建立的 sqlite 连接
    :param input_event_id: 任务输入事件 ID
    :param current_event_id: 当前状态对应的事件 ID
    :param result: 任务结果
    :param ts: 生命周期更新时间戳
    :return: 是否更新到记录
    :rtype: bool
    """
    cursor = conn.execute(
        """
        UPDATE status
        SET current_event_id = ?, status = 'success', ts = ?, result_json = ?, error_type = '', error_message = ''
        WHERE input_event_id = ?
        """,
        [
            int(current_event_id),
            ts,
            json.dumps(result, ensure_ascii=False),
            int(input_event_id),
        ],
    )
    return cursor.rowcount > 0


def promote_record_to_skipped_by_input_event_id(
    conn: sqlite3.Connection,
    input_event_id: int,
    current_event_id: int,
    *,
    ts: float,
) -> bool:
    """
    在给定连接上按 ``input_event_id`` 将状态晋升为 skipped，并推进当前事件指针。

    :param conn: 已建立的 sqlite 连接
    :param input_event_id: 任务输入事件 ID
    :param current_event_id: 晋升 skipped 后的当前事件 ID
    :param ts: 生命周期更新时间戳
    :return: 是否更新到记录
    :rtype: bool
    """
    cursor = conn.execute(
        """
        UPDATE status
        SET current_event_id = ?, ts = ?, status = 'skipped', error_type = '', error_message = ''
        WHERE input_event_id = ?
        """,
        [int(current_event_id), ts, int(input_event_id)],
    )
    return cursor.rowcount > 0


def update_retry_by_input_event_id(
    conn: sqlite3.Connection,
    input_event_id: int,
    current_event_id: int,
    *,
    ts: float,
    retry_times: int,
    error_type: str = "",
    error_message: str = "",
) -> bool:
    """
    在给定连接上按 ``input_event_id`` 更新 pending 状态的重试信息。

    记录保持 pending 状态不变，仅更新重试次数与最近一次失败的错误信息。

    :param conn: 已建立的 sqlite 连接
    :param input_event_id: 任务输入事件 ID
    :param current_event_id: 当前状态对应的最新事件 ID
    :param ts: 生命周期更新时间戳
    :param retry_times: 已重试次数
    :param error_type: 最近一次失败的错误类型，默认空字符串
    :param error_message: 最近一次失败的错误消息，默认空字符串
    :return: 是否更新到记录
    :rtype: bool
    """
    cursor = conn.execute(
        """
        UPDATE status
        SET current_event_id = ?, retry_times = ?, ts = ?, error_type = ?, error_message = ?
        WHERE input_event_id = ?
        """,
        [
            int(current_event_id),
            int(retry_times),
            ts,
            error_type,
            error_message,
            int(input_event_id),
        ],
    )
    return cursor.rowcount > 0


def delete_record_by_input_event_id(
    conn: sqlite3.Connection,
    input_event_id: int,
) -> bool:
    """
    在给定连接上按 ``input_event_id`` 删除状态。

    :param conn: 已建立的 sqlite 连接
    :param input_event_id: 待删除的任务输入事件 ID
    :return: 是否删除到状态
    :rtype: bool
    """
    cursor = conn.execute(
        "DELETE FROM status WHERE input_event_id = ?",
        [int(input_event_id)],
    )
    return cursor.rowcount > 0


def load_event_record(
    db_path: str | Path,
    event_id: int,
) -> dict[str, Any] | None:
    """
    自行创建并关闭连接，读取指定 event_id 的事件记录。

    :param db_path: sqlite 数据库文件路径
    :param event_id: 待读取的事件 ID
    :return: 事件记录字典；不存在时返回 ``None``
    :rtype: dict[str, Any] | None
    """
    conn = connect_db(db_path)
    try:
        row = conn.execute(
            """
            SELECT event_id, event_type, node, ts
            FROM events
            WHERE event_id = ?
            """,
            [int(event_id)],
        ).fetchone()
        if row is None:
            return None
        return row_to_event_dict(row)
    finally:
        conn.close()


def load_event_parent_ids(
    db_path: str | Path,
    event_id: int,
) -> list[int]:
    """
    自行创建并关闭连接，读取指定 event_id 的全部父事件 ID。

    :param db_path: sqlite 数据库文件路径
    :param event_id: 待读取的事件 ID
    :return: 父事件 ID 列表，按升序排列
    :rtype: list[int]
    """
    conn = connect_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT parent_id
            FROM event_parents
            WHERE event_id = ?
            ORDER BY parent_id ASC
            """,
            [int(event_id)],
        ).fetchall()
        return [int(row["parent_id"]) for row in rows]
    finally:
        conn.close()


def load_tasks_grouped_by_node(
    db_path: str | Path,
    statuses: Iterable[str] = ("failed", "pending"),
) -> dict[str, list[dict[str, Any]]]:
    """
    自行创建并关闭连接，按 node 分组读取指定状态的记录。

    :param db_path: sqlite 数据库文件路径
    :param statuses: 记录状态过滤条件；可传单个状态或状态列表
    :return: ``{node_name: [{"task_json": task, "error_type": str, "status": str}, ...], ...}``
    :rtype: dict[str, list[dict[str, Any]]]
    """
    conn = connect_db(db_path)
    try:
        if not statuses:
            return {}

        placeholders = ", ".join("?" for _ in statuses)
        rows = conn.execute(
            f"""
            SELECT node, task_json, error_type, status
            FROM status
            WHERE status IN ({placeholders})
            ORDER BY node ASC, id ASC
            """,
            tuple(statuses),
        ).fetchall()

        grouped_records: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            node_name = str(row["node"])
            task_json = str(row["task_json"])
            error_type = str(row["error_type"])
            status = str(row["status"])

            node_tasks = grouped_records.setdefault(node_name, [])
            node_tasks.append(
                {
                    "task_json": json.loads(task_json),
                    "error_type": error_type,
                    "status": status,
                }
            )
        return grouped_records
    finally:
        conn.close()


def load_task_error_records(
    db_path: str | Path, node: str
) -> list[tuple[Any, tuple[str, str]]]:
    """
    自行创建并关闭连接，读取指定 node 的失败任务与记录配对列表。

    :param db_path: sqlite 数据库文件路径
    :param node: 待读取的 node 名称
    :return: ``[(task, error_record), ...]``
    :rtype: list[tuple[Any, tuple[str, str]]]
    """
    conn = connect_db(db_path)
    try:
        # 读取任务与错误信息的配对原始行，供后续组装业务对象。
        rows = conn.execute(
            """
            SELECT error_type, error_message, task_json
            FROM status
            WHERE status = 'failed' AND node = ?
            ORDER BY id ASC
            """,
            [node],
        ).fetchall()
        return [
            (
                json.loads(str(row["task_json"])),
                (str(row["error_type"]), str(row["error_message"])),
            )
            for row in rows
        ]
    finally:
        conn.close()


def load_task_result_records(db_path: str | Path, node: str) -> list[tuple[Any, Any]]:
    """
    自行创建并关闭连接，读取指定 node 的任务与成功结果配对列表。

    :param db_path: sqlite 数据库文件路径
    :param node: 待读取的 node 名称
    :return: ``[(task, result), ...]``
    :rtype: list[tuple[Any, Any]]
    """
    conn = connect_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT task_json, result_json
            FROM status
            WHERE status = 'success' AND node = ?
            ORDER BY id ASC
            """,
            [node],
        ).fetchall()
        return [
            (
                json.loads(str(row["task_json"])),
                json.loads(str(row["result_json"])),
            )
            for row in rows
        ]
    finally:
        conn.close()
