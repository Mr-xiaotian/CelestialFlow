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
    在给定连接上确保记录表与索引存在。

    :param conn: 已建立的 sqlite 连接
    :return: None
    """
    # 创建错误主表。
    _ = conn.execute(
        """
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
        """
    )
    # 兼容旧库：为缺少 retry_times 列的历史表补充默认列。
    columns = {
        str(row["name"])
        for row in conn.execute("PRAGMA table_info(records)").fetchall()
    }
    if "retry_times" not in columns:
        _ = conn.execute(
            "ALTER TABLE records ADD COLUMN retry_times INTEGER NOT NULL DEFAULT 0"
        )
    # 为常用查询条件建立索引，减少筛选和排序开销。
    _ = conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_records_event_id ON records(event_id)"
    )
    _ = conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_records_status_id ON records(status, id)"
    )
    conn.commit()


# ==== 记录序列化工具 ====


def normalize_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """
    将记录归一化为 sqlite 可写格式。

    非业务记录会返回 ``None``。业务记录必须显式提供 ``node`` 与
    ``status``，由调用方保证写入语义完整。

    :param record: 原始记录字典
    :return: 可直接写入 sqlite 的参数字典，或 ``None``
    :rtype: dict[str, Any] | None
    """
    event_id = record.get("event_id")
    if event_id is None:
        return None

    return {
        "event_id": int(event_id),
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
    将 sqlite 行转换为对外记录字典。

    :param row: sqlite 查询结果中的单行
    :return: 面向上层调用方的记录字典
    :rtype: dict[str, Any]
    """
    return {
        "id": int(row["id"]),
        "event_id": int(row["event_id"]),
        "ts": float(row["ts"]),
        "node": str(row["node"]),
        "status": str(row["status"]),
        "error_type": str(row["error_type"]),
        "error_message": str(row["error_message"]),
        "task_json": json.loads(str(row["task_json"])),
        "result_json": json.loads(str(row["result_json"])),
        "retry_times": int(row["retry_times"]),
    }


# ==== 复用已有连接的写操作 ====


def insert_record(conn: sqlite3.Connection, record: dict[str, Any]) -> bool:
    """
    在给定连接上插入单条记录。

    元信息记录会被忽略。

    :param conn: 已建立的 sqlite 连接
    :param record: 原始错误记录字典
    :return: 是否实际插入了一条记录
    :rtype: bool
    """
    normalized = normalize_record(record)
    if normalized is None:
        return False

    # 插入单条归一化后的记录。
    _ = conn.execute(
        """
        INSERT INTO records (
            event_id, ts, node, status, error_type, error_message, task_json, result_json
            , retry_times
        )
        VALUES (
            :event_id, :ts, :node, :status, :error_type, :error_message, :task_json, :result_json
            , :retry_times
        )
        """,
        normalized,
    )
    return True


def promote_record_to_failed_by_event_id(
    conn: sqlite3.Connection,
    event_id: int,
    new_event_id: int,
    *,
    ts: float,
    error_type: str = "",
    error_message: str = "",
) -> bool:
    """
    在给定连接上按 ``event_id`` 将记录晋升为 failed，并切换到新的事件 ID。

    :param conn: 已建立的 sqlite 连接
    :param event_id: 当前事件 ID
    :param new_event_id: 晋升 failed 后的新事件 ID
    :param ts: 生命周期更新时间戳
    :param error_type: 错误类型，默认空字符串
    :param error_message: 错误消息，默认空字符串
    :return: 是否更新到记录
    :rtype: bool
    """
    cursor = conn.execute(
        """
        UPDATE records
        SET event_id = ?, ts = ?, status = 'failed', error_type = ?, error_message = ?
        WHERE event_id = ?
        """,
        [int(new_event_id), ts, error_type, error_message, int(event_id)],
    )
    return cursor.rowcount > 0


def promote_record_to_success_by_event_id(
    conn: sqlite3.Connection,
    event_id: int,
    result: Any,
    *,
    ts: float,
) -> bool:
    """
    在给定连接上按 ``event_id`` 将记录晋升为 success，并写入结果。

    :param conn: 已建立的 sqlite 连接
    :param event_id: 当前事件 ID
    :param result: 任务结果
    :param ts: 生命周期更新时间戳
    :return: 是否更新到记录
    :rtype: bool
    """
    cursor = conn.execute(
        """
        UPDATE records
        SET status = 'success', ts = ?, result_json = ?, error_type = '', error_message = ''
        WHERE event_id = ?
        """,
        [ts, json.dumps(result, ensure_ascii=False), int(event_id)],
    )
    return cursor.rowcount > 0


def promote_record_to_skipped_by_event_id(
    conn: sqlite3.Connection,
    event_id: int,
    new_event_id: int,
    *,
    ts: float,
) -> bool:
    """
    在给定连接上按 ``event_id`` 将记录晋升为 skipped，并切换到新的事件 ID。

    :param conn: 已建立的 sqlite 连接
    :param event_id: 当前事件 ID
    :param new_event_id: 晋升 skipped 后的新事件 ID
    :param ts: 生命周期更新时间戳
    :return: 是否更新到记录
    :rtype: bool
    """
    cursor = conn.execute(
        """
        UPDATE records
        SET event_id = ?, ts = ?, status = 'skipped', error_type = '', error_message = ''
        WHERE event_id = ?
        """,
        [int(new_event_id), ts, int(event_id)],
    )
    return cursor.rowcount > 0


def update_retry_by_event_id(
    conn: sqlite3.Connection,
    event_id: int,
    *,
    ts: float,
    retry_times: int,
    error_type: str = "",
    error_message: str = "",
) -> bool:
    """
    在给定连接上按 ``event_id`` 更新 pending 记录的重试信息。

    记录保持 pending 状态不变，仅更新重试次数与最近一次失败的错误信息。

    :param conn: 已建立的 sqlite 连接
    :param event_id: 当前事件 ID
    :param ts: 生命周期更新时间戳
    :param retry_times: 已重试次数
    :param error_type: 最近一次失败的错误类型，默认空字符串
    :param error_message: 最近一次失败的错误消息，默认空字符串
    :return: 是否更新到记录
    :rtype: bool
    """
    cursor = conn.execute(
        """
        UPDATE records
        SET retry_times = ?, ts = ?, error_type = ?, error_message = ?
        WHERE event_id = ?
        """,
        [int(retry_times), ts, error_type, error_message, int(event_id)],
    )
    return cursor.rowcount > 0


def delete_record_by_event_id(conn: sqlite3.Connection, event_id: int) -> bool:
    """
    在给定连接上按 ``event_id`` 删除记录。

    :param conn: 已建立的 sqlite 连接
    :param event_id: 待删除的事件 ID
    :return: 是否删除到记录
    :rtype: bool
    """
    cursor = conn.execute(
        "DELETE FROM records WHERE event_id = ?",
        [int(event_id)],
    )
    return cursor.rowcount > 0


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
            FROM records
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
            FROM records
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
            FROM records
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
