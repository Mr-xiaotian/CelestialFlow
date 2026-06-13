# persistence/util_sqlite.py
from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..runtime.util_types import PersistedErrorRecord


def connect_errors_db(db_path: str | Path) -> sqlite3.Connection:
    """
    连接错误数据库并确保表结构与索引存在。

    :param db_path: sqlite 数据库文件路径
    :return: 可直接用于错误读写的 sqlite 连接
    :rtype: sqlite3.Connection
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ = conn.execute("PRAGMA journal_mode=WAL")
    _ = conn.execute("PRAGMA synchronous=NORMAL")
    _ = conn.execute("PRAGMA foreign_keys=ON")
    _ensure_errors_table(conn)
    return conn


def _ensure_errors_table(conn: sqlite3.Connection) -> None:
    """
    创建错误记录表与索引。

    :param conn: 已建立的 sqlite 连接
    :return: None
    """
    _ = conn.execute(
        """
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL DEFAULT 0,
            stage TEXT NOT NULL DEFAULT '',
            error_id INTEGER,
            error_type TEXT NOT NULL DEFAULT '',
            error_message TEXT NOT NULL DEFAULT '',
            task_json TEXT NOT NULL DEFAULT 'null'
        )
        """
    )
    _ = conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_errors_ts ON errors(ts)"
    )
    _ = conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_errors_stage_ts ON errors(stage, ts)"
    )
    _ = conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_errors_type_ts ON errors(error_type, ts)"
    )
    _ = conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_errors_error_id ON errors(error_id)"
    )
    conn.commit()


def normalize_error_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """
    将错误记录归一化为 sqlite 可写格式。

    非错误元信息记录会返回 ``None``。

    :param record: 原始错误记录字典
    :return: 可直接写入 sqlite 的参数字典，或 ``None``
    :rtype: dict[str, Any] | None
    """
    if record.get("error_id") is None:
        return None

    task_value = record["task_json"] if "task_json" in record else record.get("task")
    return {
        "ts": float(record.get("ts", 0.0) or 0.0),
        "stage": str(record.get("stage", "") or ""),
        "error_id": (
            int(record["error_id"])
            if record.get("error_id") is not None
            else None
        ),
        "error_type": str(record.get("error_type", "") or ""),
        "error_message": str(record.get("error_message", "") or ""),
        "task_json": json.dumps(task_value, ensure_ascii=False),
    }


def insert_error_record(conn: sqlite3.Connection, record: dict[str, Any]) -> bool:
    """
    插入单条错误记录。

    元信息记录会被忽略。

    :param conn: 已建立的 sqlite 连接
    :param record: 原始错误记录字典
    :return: 是否实际插入了一条错误记录
    :rtype: bool
    """
    normalized = normalize_error_record(record)
    if normalized is None:
        return False
    _ = conn.execute(
        """
        INSERT INTO errors (ts, stage, error_id, error_type, error_message, task_json)
        VALUES (:ts, :stage, :error_id, :error_type, :error_message, :task_json)
        """,
        normalized,
    )
    return True


def replace_error_records(
    db_path: str | Path, errors: Iterable[dict[str, Any]]
) -> None:
    """
    用给定错误列表覆盖数据库中的全部错误记录。

    :param db_path: sqlite 数据库文件路径
    :param errors: 待写入的错误记录迭代器
    :return: None
    """
    conn = connect_errors_db(db_path)
    try:
        _ = conn.execute("DELETE FROM errors")
        normalized_rows = [
            normalized
            for item in errors
            if (normalized := normalize_error_record(item)) is not None
        ]
        if normalized_rows:
            _ = conn.executemany(
                """
                INSERT INTO errors (
                    ts, stage, error_id, error_type, error_message, task_json
                )
                VALUES (:ts, :stage, :error_id, :error_type, :error_message, :task_json)
                """,
                normalized_rows,
            )
        conn.commit()
    finally:
        conn.close()


def append_error_records(
    db_path: str | Path, errors: Iterable[dict[str, Any]]
) -> int:
    """
    将给定错误列表追加写入数据库。

    :param db_path: sqlite 数据库文件路径
    :param errors: 待追加的错误记录迭代器
    :return: 实际追加写入的错误记录数量
    :rtype: int
    """
    conn = connect_errors_db(db_path)
    try:
        inserted = 0
        for item in errors:
            if insert_error_record(conn, item):
                inserted += 1
        conn.commit()
        return inserted
    finally:
        conn.close()


def _decode_task_json(task_json: str) -> Any:
    """
    从 ``task_json`` 列反序列化任务对象。

    :param task_json: 数据库中的任务 JSON 字符串
    :return: 反序列化后的任务对象
    :rtype: Any
    """
    return json.loads(task_json)


def row_to_error_dict(row: sqlite3.Row) -> dict[str, Any]:
    """
    将 sqlite 行转换为对外错误字典。

    :param row: sqlite 查询结果中的单行
    :return: 面向上层调用方的错误记录字典
    :rtype: dict[str, Any]
    """
    return {
        "id": int(row["id"]),
        "ts": float(row["ts"]),
        "stage": str(row["stage"]),
        "error_id": row["error_id"],
        "error_type": str(row["error_type"]),
        "error_message": str(row["error_message"]),
        "task": _decode_task_json(str(row["task_json"])),
    }


def load_error_records(db_path: str | Path) -> list[dict[str, Any]]:
    """
    读取数据库中的全部错误记录。

    :param db_path: sqlite 数据库文件路径
    :return: 全量错误记录列表
    :rtype: list[dict[str, Any]]
    """
    conn = connect_errors_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, ts, stage, error_id, error_type, error_message, task_json
            FROM errors
            ORDER BY id ASC
            """
        ).fetchall()
        return [row_to_error_dict(row) for row in rows]
    finally:
        conn.close()


def load_error_records_after(
    db_path: str | Path, after_row_id: int
) -> list[dict[str, Any]]:
    """
    读取指定 row id 之后的全部错误记录。

    :param db_path: sqlite 数据库文件路径
    :param after_row_id: 已同步到的最大错误行号
    :return: 增量错误记录列表
    :rtype: list[dict[str, Any]]
    """
    conn = connect_errors_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, ts, stage, error_id, error_type, error_message, task_json
            FROM errors
            WHERE id > ?
            ORDER BY id ASC
            """,
            [after_row_id],
        ).fetchall()
        return [row_to_error_dict(row) for row in rows]
    finally:
        conn.close()


def get_max_error_row_id(db_path: str | Path) -> int:
    """
    获取数据库中当前最大的错误行号。

    :param db_path: sqlite 数据库文件路径
    :return: 当前最大的错误行号；无记录时返回 0
    :rtype: int
    """
    conn = connect_errors_db(db_path)
    try:
        row = conn.execute("SELECT COALESCE(MAX(id), 0) FROM errors").fetchone()
        return int(row[0]) if row is not None else 0
    finally:
        conn.close()


def query_error_records(
    db_path: str | Path,
    page: int,
    page_size: int,
    node: str,
    keyword: str,
    sort_order: str,
) -> tuple[int, int, list[dict[str, Any]]]:
    """
    按条件查询错误记录并返回分页结果。

    :param db_path: sqlite 数据库文件路径
    :param page: 请求页码
    :param page_size: 每页大小
    :param node: 节点名称过滤条件
    :param keyword: 关键词过滤条件
    :param sort_order: 排序方式，支持 ``newest`` 或 ``oldest``
    :return: ``(total, total_pages, page_items)``
    :rtype: tuple[int, int, list[dict[str, Any]]]
    """
    conn = connect_errors_db(db_path)
    try:
        where_clauses: list[str] = []
        params: list[Any] = []
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
                f"SELECT COUNT(*) FROM errors {where_sql}",
                params,
            ).fetchone()[0]
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        normalized_page = min(page, total_pages)
        sort_sql = "ASC" if sort_order == "oldest" else "DESC"
        offset = (normalized_page - 1) * page_size
        rows = conn.execute(
            f"""
            SELECT id, ts, stage, error_id, error_type, error_message, task_json
            FROM errors
            {where_sql}
            ORDER BY ts {sort_sql}, id {sort_sql}
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, offset],
        ).fetchall()
        return total, total_pages, [row_to_error_dict(row) for row in rows]
    finally:
        conn.close()


def load_task_error_pairs(db_path: str | Path) -> list[tuple[Any, PersistedErrorRecord]]:
    """
    读取错误数据库并返回任务与错误记录的配对列表。

    :param db_path: sqlite 数据库文件路径
    :return: ``[(task, error_record), ...]``
    :rtype: list[tuple[Any, PersistedErrorRecord]]
    """
    conn = connect_errors_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT ts, stage, error_id, error_type, error_message, task_json
            FROM errors
            ORDER BY id ASC
            """
        ).fetchall()
        return [
            (
                _decode_task_json(str(row["task_json"])),
                PersistedErrorRecord(
                    ts=float(row["ts"]),
                    stage=str(row["stage"]),
                    error_id=int(row["error_id"]) if row["error_id"] is not None else None,
                    error_type=str(row["error_type"]),
                    error_message=str(row["error_message"]),
                ),
            )
            for row in rows
        ]
    finally:
        conn.close()


def load_task_by_stage(db_path: str | Path) -> dict[str, list[Any]]:
    """
    按 ``stage`` 聚合失败任务。

    :param db_path: sqlite 数据库文件路径
    :return: 以 stage 名称分组的失败任务字典
    :rtype: dict[str, list[Any]]
    """
    grouped: dict[str, list[Any]] = defaultdict(list)
    for task, error in load_task_error_pairs(db_path):
        grouped[error.stage].append(task)
    return dict(grouped)
