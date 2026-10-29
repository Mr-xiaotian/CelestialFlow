import json
import sqlite3

import pytest

from celestialflow.persist.util_sqlite import (
    connect_db,
    delete_record_by_event_id,
    insert_record,
    load_task_error_records,
    load_task_result_records,
    normalize_record,
    promote_record_to_failed_by_event_id,
    promote_record_to_success_by_event_id,
    row_to_record_dict,
    update_retry_by_event_id,
)


def _insert_records(sqlite_path, records: list[dict[str, object]]) -> int:
    """测试辅助：直接向 sqlite 追加记录，重复 event_id 时跳过。"""
    conn = connect_db(sqlite_path)
    try:
        inserted = 0
        for record in records:
            try:
                if insert_record(conn, record):
                    inserted += 1
            except sqlite3.IntegrityError:
                continue
        conn.commit()
        return inserted
    finally:
        conn.close()


def _fetch_records(sqlite_path, status: str = "failed") -> list[dict[str, object]]:
    """测试辅助：按状态读取当前 sqlite 中的记录。"""
    conn = connect_db(sqlite_path)
    try:
        rows = conn.execute(
            """
            SELECT id, event_id, ts, node, status, error_type, error_message, task_json
                 , result_json, retry_times
            FROM records
            WHERE status = ?
            ORDER BY id ASC
            """,
            [status],
        ).fetchall()
        return [row_to_record_dict(row) for row in rows]
    finally:
        conn.close()


@pytest.fixture
def sample_errors():
    """创建一组用于 sqlite 错误工具测试的样本记录。"""
    return [
        {"timestamp": "meta-only", "graph_name": "demo"},
        {
            "ts": 1.0,
            "node": "s1",
            "status": "failed",
            "event_id": 1,
            "error_type": "ValueError",
            "error_message": "bad value",
            "task_json": {"id": 1, "label": "TaskOne"},
        },
        {
            "ts": 2.0,
            "node": "s2",
            "status": "failed",
            "event_id": 2,
            "error_type": "RuntimeError",
            "error_message": "boom happened",
            "task_json": ["A", "B"],
        },
        {
            "ts": 3.0,
            "node": "s1",
            "status": "failed",
            "event_id": 3,
            "error_type": "TypeError",
            "error_message": "wrong type",
            "task_json": "PlainTask",
        },
    ]


@pytest.fixture
def sqlite_path(tmp_path):
    """创建临时 sqlite 文件路径。"""
    return tmp_path / "records.sqlite3"


class TestSpliteUtils:
    def test_connect_db_creates_table_and_indices(self, sqlite_path):
        """测试建立连接时会自动创建 records 表和必要索引。"""
        conn = connect_db(sqlite_path)
        try:
            table_names = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            index_names = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index'"
                ).fetchall()
            }
            index_list = conn.execute("PRAGMA index_list(records)").fetchall()
            result_info = conn.execute("PRAGMA table_info(records)").fetchall()
        finally:
            conn.close()

        assert "records" in table_names
        assert "idx_records_event_id" in index_names
        assert "idx_records_status_id" in index_names
        assert any(row[1] == "idx_records_event_id" and row[2] == 1 for row in index_list)
        assert [row[1] for row in result_info] == [
            "id",
            "event_id",
            "ts",
            "node",
            "status",
            "error_type",
            "error_message",
            "task_json",
            "result_json",
            "retry_times",
        ]
        assert any(row[1] == "result_json" for row in result_info)

    def test_normalize_record(self, sample_errors):
        """测试错误记录会被归一化为 sqlite 可写格式。"""
        assert normalize_record(sample_errors[0]) is None

        normalized = normalize_record(sample_errors[1])

        assert normalized is not None
        assert normalized["event_id"] == 1
        assert normalized["node"] == "s1"
        assert normalized["status"] == "failed"
        assert normalized["error_type"] == "ValueError"
        assert normalized["error_message"] == "bad value"
        assert normalized["ts"] == 1.0
        assert normalized["retry_times"] == 0
        assert json.loads(normalized["task_json"]) == {"id": 1, "label": "TaskOne"}

    def test_normalize_record_requires_node_and_status(self):
        """测试业务记录必须显式提供 node 与 status。"""
        with pytest.raises(KeyError, match="node"):
            normalize_record({"event_id": 1, "status": "failed", "task_json": {}})

        with pytest.raises(KeyError, match="status"):
            normalize_record({"event_id": 1, "node": "s1", "task_json": {}})

    def test_insert_and_load_records(self, sqlite_path, sample_errors):
        """测试单条插入会忽略元信息，并能正常读回错误记录。"""
        conn = connect_db(sqlite_path)
        try:
            assert insert_record(conn, sample_errors[0]) is False
            assert insert_record(conn, sample_errors[1]) is True
            assert insert_record(conn, sample_errors[2]) is True
            conn.commit()
        finally:
            conn.close()

        records = _fetch_records(sqlite_path)

        assert len(records) == 2
        assert records[0]["id"] == 1
        assert records[0]["ts"] == 1.0
        assert records[0]["task_json"] == {"id": 1, "label": "TaskOne"}
        assert records[0]["result_json"] is None
        assert records[1]["id"] == 2
        assert records[1]["ts"] == 2.0
        assert records[1]["task_json"] == ["A", "B"]
        assert records[1]["result_json"] is None

    def test_promote_record_to_failed_by_event_id(self, sqlite_path, sample_errors):
        """测试按 event_id 更新记录状态与错误信息。"""
        waiting_record = {
            "event_id": 9,
            "node": "s9",
            "status": "waiting",
            "task_json": {"value": 9},
        }
        appended = _insert_records(sqlite_path, [waiting_record])
        assert appended == 1

        conn = connect_db(sqlite_path)
        try:
            updated = promote_record_to_failed_by_event_id(
                conn,
                9,
                19,
                ts=9.5,
                error_type="RuntimeError",
                error_message="boom",
            )
            conn.commit()
        finally:
            conn.close()

        assert updated is True
        failed_records = _fetch_records(sqlite_path, "failed")
        assert len(failed_records) == 1
        assert failed_records[0]["event_id"] == 19
        assert failed_records[0]["status"] == "failed"
        assert failed_records[0]["ts"] == 9.5
        assert failed_records[0]["error_type"] == "RuntimeError"
        assert failed_records[0]["error_message"] == "boom"

    def test_promote_record_to_success_by_event_id(self, sqlite_path):
        """测试按 event_id 将记录晋升为 success 并写入结果。"""
        pending_record = {
            "event_id": 8,
            "node": "s8",
            "status": "pending",
            "task_json": {"value": 8},
        }
        appended = _insert_records(sqlite_path, [pending_record])
        assert appended == 1

        conn = connect_db(sqlite_path)
        try:
            updated = promote_record_to_success_by_event_id(
                conn,
                8,
                {"ok": True, "value": [1, 2, 3]},
                ts=8.5,
            )
            conn.commit()
        finally:
            conn.close()

        assert updated is True
        success_records = _fetch_records(sqlite_path, "success")
        assert len(success_records) == 1
        assert success_records[0]["event_id"] == 8
        assert success_records[0]["status"] == "success"
        assert success_records[0]["ts"] == 8.5
        assert success_records[0]["result_json"] == {"ok": True, "value": [1, 2, 3]}
        assert success_records[0]["task_json"] == {"value": 8}

    def test_update_retry_by_event_id(self, sqlite_path):
        """测试按 event_id 更新 pending 记录的重试信息，状态保持不变。"""
        pending_record = {
            "event_id": 7,
            "node": "s7",
            "status": "pending",
            "task_json": {"value": 7},
        }
        appended = _insert_records(sqlite_path, [pending_record])
        assert appended == 1

        conn = connect_db(sqlite_path)
        try:
            updated = update_retry_by_event_id(
                conn,
                7,
                ts=7.5,
                retry_times=2,
                error_type="ValueError",
                error_message="try failed",
            )
            conn.commit()
        finally:
            conn.close()

        assert updated is True
        pending_records = _fetch_records(sqlite_path, "pending")
        assert len(pending_records) == 1
        assert pending_records[0]["status"] == "pending"
        assert pending_records[0]["retry_times"] == 2
        assert pending_records[0]["error_type"] == "ValueError"
        assert pending_records[0]["error_message"] == "try failed"
        assert pending_records[0]["ts"] == 7.5

    def test_update_retry_by_event_id_missing_record(self, sqlite_path):
        """测试更新不存在的 event_id 时应返回 False。"""
        conn = connect_db(sqlite_path)
        try:
            updated = update_retry_by_event_id(
                conn,
                999,
                ts=1.0,
                retry_times=1,
                error_type="ValueError",
                error_message="boom",
            )
            conn.commit()
        finally:
            conn.close()

        assert updated is False

    def test_delete_record_by_event_id(self, sqlite_path, sample_errors):
        """测试按 event_id 删除记录。"""
        appended = _insert_records(sqlite_path, sample_errors[1:])
        assert appended == 3

        conn = connect_db(sqlite_path)
        try:
            deleted = delete_record_by_event_id(conn, 2)
            conn.commit()
        finally:
            conn.close()

        assert deleted is True
        assert [item["event_id"] for item in _fetch_records(sqlite_path)] == [1, 3]

    def test_load_task_error_records_and_grouping(self, sqlite_path, sample_errors):
        """测试任务-错误配对读取以及按 node 聚合。"""
        appended = _insert_records(sqlite_path, sample_errors)
        assert appended == 3

        pairs = load_task_error_records(sqlite_path, "s1")
        assert len(pairs) == 2
        assert pairs[0][0] == {"id": 1, "label": "TaskOne"}
        assert pairs[0][1] == ("ValueError", "bad value")
        assert pairs[1][0] == "PlainTask"
        assert pairs[1][1] == ("TypeError", "wrong type")

    def test_load_task_result_records(self, sqlite_path):
        """测试任务-结果配对读取。"""
        pending_record = {
            "event_id": 8,
            "node": "s8",
            "status": "pending",
            "task_json": {"value": 8},
        }
        appended = _insert_records(sqlite_path, [pending_record])
        assert appended == 1

        conn = connect_db(sqlite_path)
        try:
            updated = promote_record_to_success_by_event_id(
                conn,
                8,
                {"ok": True, "value": [1, 2, 3]},
                ts=8.5,
            )
            conn.commit()
        finally:
            conn.close()

        assert updated is True
        pairs = load_task_result_records(sqlite_path, "s8")
        assert pairs == [({"value": 8}, {"ok": True, "value": [1, 2, 3]})]
