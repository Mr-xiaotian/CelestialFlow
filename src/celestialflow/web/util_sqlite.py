from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def connect_db(db_path: str | Path) -> sqlite3.Connection:
    """
    创建 sqlite 连接并交给调用方管理其生命周期。

    :param db_path: sqlite 数据库文件路径
    :return: 可直接用于记录读写的 sqlite 连接
    :rtype: sqlite3.Connection
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row

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
    _ = conn.execute(
        """
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
        """
    )
    _ = conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_records_event_id ON records(event_id)"
    )
    _ = conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_records_status_id ON records(status, id)"
    )
    conn.commit()


def normalize_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """
    将记录归一化为 sqlite 可写格式。

    :param record: 原始记录字典
    :return: 可直接写入 sqlite 的参数字典，或 ``None``
    :rtype: dict[str, Any] | None
    """
    event_id = record.get("event_id")
    if event_id is None:
        return None

    return {
        "event_id": int(event_id),
        "stage": str(record["stage"]),
        "status": str(record["status"]),
        "error_type": str(record.get("error_type", "") or ""),
        "error_message": str(record.get("error_message", "") or ""),
        "ts": float(record.get("ts", 0.0) or 0.0),
        "task_json": json.dumps(record["task_json"], ensure_ascii=False),
        "result_json": json.dumps(record.get("result_json"), ensure_ascii=False),
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
        "stage": str(row["stage"]),
        "status": str(row["status"]),
        "error_type": str(row["error_type"]),
        "error_message": str(row["error_message"]),
        "task_json": json.loads(str(row["task_json"])),
        "result_json": json.loads(str(row["result_json"])),
    }


def insert_record(conn: sqlite3.Connection, record: dict[str, Any]) -> bool:
    """
    在给定连接上插入单条记录。

    :param conn: 已建立的 sqlite 连接
    :param record: 原始错误记录字典
    :return: 是否实际插入了一条记录
    :rtype: bool
    """
    normalized = normalize_record(record)
    if normalized is None:
        return False

    _ = conn.execute(
        """
        INSERT INTO records (
            event_id, ts, stage, status, error_type, error_message, task_json, result_json
        )
        VALUES (
            :event_id, :ts, :stage, :status, :error_type, :error_message, :task_json, :result_json
        )
        """,
        normalized,
    )
    return True


def clear_records(db_path: str | Path) -> None:
    """
    自行创建并关闭连接，直接清空数据库中的全部记录。

    :param db_path: sqlite 数据库文件路径
    :return: None
    """
    conn = connect_db(db_path)
    try:
        _ = conn.execute("DELETE FROM records")
        conn.commit()
    finally:
        conn.close()


def append_records(db_path: str | Path, records: Iterable[dict[str, Any]]) -> int:
    """
    自行创建并关闭连接，将给定记录列表追加写入数据库。

    :param db_path: sqlite 数据库文件路径
    :param records: 待追加的记录迭代器
    :return: 实际追加写入的记录数量
    :rtype: int
    """
    conn = connect_db(db_path)
    try:
        inserted = 0
        for item in records:
            try:
                if insert_record(conn, item):
                    inserted += 1
            except sqlite3.IntegrityError:
                continue
        conn.commit()
        return inserted
    finally:
        conn.close()


def get_max_event_id_in_fail(db_path: str | Path) -> int | None:
    """
    自行创建并关闭连接，读取失败记录中的最大 ``event_id``。

    :param db_path: sqlite 数据库文件路径
    :return: 失败记录中的最大 ``event_id``；若不存在失败记录则返回 ``None``
    :rtype: int | None
    """
    conn = connect_db(db_path)
    try:
        row = conn.execute(
            """
            SELECT MAX(event_id) AS max_event_id
            FROM records
            WHERE status = 'failed'
            """
        ).fetchone()
        max_event_id = row["max_event_id"]
        return None if max_event_id is None else int(max_event_id)
    finally:
        conn.close()


def load_records(db_path: str | Path, status: str = "failed") -> list[dict[str, Any]]:
    """
    自行创建并关闭连接，读取数据库中指定状态的记录。

    :param db_path: sqlite 数据库文件路径
    :param status: 记录状态过滤条件，默认 ``failed``
    :return: 指定状态的记录列表
    :rtype: list[dict[str, Any]]
    """
    conn = connect_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, event_id, ts, stage, status, error_type, error_message, task_json
                 , result_json
            FROM records
            WHERE status = ?
            ORDER BY id ASC
            """,
            [status],
        ).fetchall()
        return [row_to_record_dict(row) for row in rows]
    finally:
        conn.close()


def query_records(
    db_path: str | Path,
    page: int,
    page_size: int,
    node: str,
    keyword: str,
    sort_order: str,
    status: str = "failed",
) -> tuple[int, int, list[dict[str, Any]]]:
    """
    自行创建并关闭连接，按条件查询指定状态的记录并返回分页结果。

    :param db_path: sqlite 数据库文件路径
    :param page: 请求页码
    :param page_size: 每页大小
    :param node: 节点名称过滤条件
    :param keyword: 关键词过滤条件
    :param sort_order: 排序方式，支持 ``newest`` 或 ``oldest``
    :param status: 记录状态过滤条件，默认 ``failed``
    :return: ``(total, total_pages, page_items)``
    :rtype: tuple[int, int, list[dict[str, Any]]]
    """
    conn = connect_db(db_path)
    try:
        where_clauses: list[str] = ["status = ?"]
        params: list[Any] = [status]
        if node:
            where_clauses.append("stage = ?")
            params.append(node)
        if keyword:
            like_pattern = f"%{keyword.lower()}%"
            where_clauses.append(
                "(LOWER(error_type) LIKE ? OR LOWER(error_message) LIKE ? OR LOWER(task_json) LIKE ?)"
            )
            params.extend([like_pattern, like_pattern, like_pattern])

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        total = int(
            conn.execute(
                f"SELECT COUNT(*) FROM records {where_sql}",
                params,
            ).fetchone()[0]
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        normalized_page = min(page, total_pages)
        sort_sql = "ASC" if sort_order == "oldest" else "DESC"
        offset = (normalized_page - 1) * page_size

        rows = conn.execute(
            f"""
            SELECT id, event_id, ts, stage, status, error_type, error_message, task_json
                 , result_json
            FROM records
            {where_sql}
            ORDER BY ts {sort_sql}, id {sort_sql}
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, offset],
        ).fetchall()

        return total, total_pages, [row_to_record_dict(row) for row in rows]
    finally:
        conn.close()


def query_error_type_counts(
    db_path: str | Path,
    node: str = "",
    status: str = "failed",
) -> list[dict[str, Any]]:
    """
    自行创建并关闭连接，按错误类型聚合指定状态的记录数量。

    :param db_path: sqlite 数据库文件路径
    :param node: 节点名称过滤条件；为空时统计全部节点
    :param status: 记录状态过滤条件，默认 ``failed``
    :return: ``[{"error_type": str, "count": int}, ...]``
    :rtype: list[dict[str, Any]]
    """
    conn = connect_db(db_path)
    try:
        where_clauses: list[str] = ["status = ?"]
        params: list[Any] = [status]
        if node:
            where_clauses.append("stage = ?")
            params.append(node)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        rows = conn.execute(
            f"""
            SELECT error_type, COUNT(*) AS count
            FROM records
            {where_sql}
            GROUP BY error_type
            ORDER BY count DESC, error_type ASC
            """,
            params,
        ).fetchall()
        return [
            {
                "error_type": str(row["error_type"]),
                "count": int(row["count"]),
            }
            for row in rows
        ]
    finally:
        conn.close()
