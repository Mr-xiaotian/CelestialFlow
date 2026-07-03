# persistence/util_sqlite.py
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

# ==== 工具函数：不自持完整 conn 生命周期 ====


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
    )  # 允许跨线程使用, 由于使用端spout指挥存在单条流离线程, 这里是安全的
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
            stage TEXT NOT NULL,
            status TEXT NOT NULL,
            error_type TEXT NOT NULL DEFAULT '',
            error_message TEXT NOT NULL DEFAULT '',
            task_json TEXT NOT NULL,
            result_json TEXT NOT NULL DEFAULT 'null'
        )
        """
    )
    # 为常用查询条件建立索引，减少筛选和排序开销。
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

    非业务记录会返回 ``None``。业务记录必须显式提供 ``stage`` 与
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
            event_id, ts, stage, status, error_type, error_message, task_json, result_json
        )
        VALUES (
            :event_id, :ts, :stage, :status, :error_type, :error_message, :task_json, :result_json
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
    :param ts: 生命周期更新时间戳，默认 ``None``
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
    :param ts: 生命周期更新时间戳，默认 ``None``
    :return: 是否更新到记录
    :rtype: bool
    """
    cursor = conn.execute(
        """
        UPDATE records
        SET status = 'success', ts = ?, result_json = ?
        WHERE event_id = ?
        """,
        [ts, json.dumps(result, ensure_ascii=False), int(event_id)],
    )
    return cursor.rowcount > 0


def update_record_event_id_by_event_id(
    conn: sqlite3.Connection,
    event_id: int,
    new_event_id: int,
    *,
    ts: float,
) -> bool:
    """
    在给定连接上按 ``event_id`` 更新记录的 ``event_id``。

    该操作用于任务重试时，将待处理记录绑定到新的运行事件 ID。

    :param conn: 已建立的 sqlite 连接
    :param event_id: 旧事件 ID
    :param new_event_id: 新事件 ID
    :param ts: 生命周期更新时间戳，默认 ``None``
    :return: 是否更新到记录
    :rtype: bool
    """
    cursor = conn.execute(
        """
        UPDATE records
        SET event_id = ?, ts = ?
        WHERE event_id = ?
        """,
        [int(new_event_id), ts, int(event_id)],
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


# ==== 自持完整 conn 生命周期的读写函数 ====


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
                # event_id 已存在时跳过，保证增量同步接口具备幂等性。
                continue
        conn.commit()
        return inserted
    finally:
        conn.close()


def load_records(
    db_path: str | Path,
    status: str = "failed",
) -> list[dict[str, Any]]:
    """
    自行创建并关闭连接，读取数据库中指定状态的记录。

    :param db_path: sqlite 数据库文件路径
    :param status: 记录状态过滤条件，默认 ``failed``
    :return: 指定状态的记录列表
    :rtype: list[dict[str, Any]]
    """
    conn = connect_db(db_path)
    try:
        # 按写入顺序读取指定状态的记录。
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


def load_records_grouped_by_stage(
    db_path: str | Path,
    status: str = "failed",
) -> dict[str, list[dict[str, Any]]]:
    """
    自行创建并关闭连接，按 stage 分组读取指定状态的记录。

    :param db_path: sqlite 数据库文件路径
    :param status: 记录状态过滤条件，默认 ``failed``
    :return: ``{stage_name: [record, ...], ...}``
    :rtype: dict[str, list[dict[str, Any]]]
    """
    conn = connect_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, event_id, ts, stage, status, error_type, error_message, task_json
                 , result_json
            FROM records
            WHERE status = ?
            ORDER BY stage ASC, id ASC
            """,
            [status],
        ).fetchall()

        grouped_records: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            stage_name = str(row["stage"])
            stage_tasks = grouped_records.setdefault(stage_name, [])
            stage_tasks.append(row_to_record_dict(row))
        return grouped_records
    finally:
        conn.close()


def load_tasks_grouped_by_stage(
    db_path: str | Path,
    status: str = "failed",
) -> dict[str, list[dict[str, Any]]]:
    """
    自行创建并关闭连接，按 stage 分组读取指定状态的记录。

    :param db_path: sqlite 数据库文件路径
    :param status: 记录状态过滤条件，默认 ``failed``
    :return: ``{stage_name: [record, ...], ...}``
    :rtype: dict[str, list[dict[str, Any]]]
    """
    conn = connect_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT stage, task_json
            FROM records
            WHERE status = ?
            ORDER BY stage ASC, id ASC
            """,
            [status],
        ).fetchall()

        grouped_records: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            stage_name = str(row["stage"])
            task_json = str(row["task_json"])
            stage_tasks = grouped_records.setdefault(stage_name, [])
            stage_tasks.append(json.loads(task_json))
        return grouped_records
    finally:
        conn.close()


def load_records_after_event_id_in_fail(
    db_path: str | Path,
    min_event_id: int,
) -> list[dict[str, Any]]:
    """
    自行创建并关闭连接，读取失败记录中 ``event_id`` 大于给定下界的条目。

    :param db_path: sqlite 数据库文件路径
    :param min_event_id: 失败记录的 ``event_id`` 下界
    :return: 命中的失败记录列表
    :rtype: list[dict[str, Any]]
    """
    conn = connect_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, event_id, ts, stage, status, error_type, error_message, task_json
                    , result_json
            FROM records
            WHERE status = 'failed' AND event_id > ?
            ORDER BY event_id ASC
            """,
            [int(min_event_id)],
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
        # 构造动态筛选条件与参数。
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

        # 先查询总数，并据此归一化分页参数。
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

        # 查询当前页数据；按 ts 和 id 排序以保持稳定顺序。
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

        # 转换为上层使用的错误字典格式。
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


def load_task_error_records(
    db_path: str | Path, stage: str
) -> list[tuple[Any, tuple[str, str]]]:
    """
    自行创建并关闭连接，读取指定 stage 的失败任务与记录配对列表。

    :param db_path: sqlite 数据库文件路径
    :param stage: 待读取的 stage 名称
    :return: ``[(task, error_record), ...]``
    :rtype: list[tuple[Any, tuple[str, str]]]]
    """
    conn = connect_db(db_path)
    try:
        # 读取任务与错误信息的配对原始行，供后续组装业务对象。
        rows = conn.execute(
            """
            SELECT error_type, error_message, task_json
            FROM records
            WHERE status = 'failed' AND stage = ?
            ORDER BY id ASC
            """,
            [stage],
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


def load_task_result_records(db_path: str | Path, stage: str) -> list[tuple[Any, Any]]:
    """
    自行创建并关闭连接，读取指定 stage 的任务与成功结果配对列表。

    :param db_path: sqlite 数据库文件路径
    :param stage: 待读取的 stage 名称
    :return: ``[(task, result), ...]``
    :rtype: list[tuple[Any, Any]]
    """
    conn = connect_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT task_json, result_json
            FROM records
            WHERE status = 'success' AND stage = ?
            ORDER BY id ASC
            """,
            [stage],
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
