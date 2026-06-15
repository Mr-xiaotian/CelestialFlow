import json

import pytest

from celestialflow.persistence.util_sqlite import (
    append_records,
    connect_db,
    delete_record_by_event_id,
    get_event_ids,
    insert_record,
    load_records,
    load_records_by_event_ids,
    load_task_records,
    normalize_record,
    query_records,
    replace_records,
    promote_record_to_failed_by_event_id,
    update_record_event_id_by_event_id,
)


@pytest.fixture
def sample_errors():
    """创建一组用于 sqlite 错误工具测试的样本记录。"""
    return [
        {"timestamp": "meta-only", "graph_name": "demo"},
        {
            "error_ts": 1.0,
            "stage": "s1",
            "event_id": 1,
            "error_type": "ValueError",
            "error_message": "bad value",
            "task": {"id": 1, "label": "TaskOne"},
        },
        {
            "error_ts": 2.0,
            "stage": "s2",
            "event_id": 2,
            "error_type": "RuntimeError",
            "error_message": "boom happened",
            "task": ["A", "B"],
        },
        {
            "error_ts": 3.0,
            "stage": "s1",
            "event_id": 3,
            "error_type": "TypeError",
            "error_message": "wrong type",
            "task": "PlainTask",
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
        finally:
            conn.close()

        assert "records" in table_names
        assert "idx_records_error_ts" in index_names
        assert "idx_records_stage_error_ts" in index_names
        assert "idx_records_type_error_ts" in index_names
        assert "idx_records_event_id" in index_names

    def test_normalize_record(self, sample_errors):
        """测试错误记录会被归一化为 sqlite 可写格式。"""
        assert normalize_record(sample_errors[0]) is None

        normalized = normalize_record(sample_errors[1])

        assert normalized is not None
        assert normalized["event_id"] == 1
        assert normalized["stage"] == "s1"
        assert normalized["status"] == "failed"
        assert normalized["error_type"] == "ValueError"
        assert normalized["error_message"] == "bad value"
        assert normalized["error_ts"] == 1.0
        assert json.loads(normalized["task_json"]) == {"id": 1, "label": "TaskOne"}

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

        records = load_records(sqlite_path)

        assert len(records) == 2
        assert records[0]["id"] == 1
        assert records[0]["task"] == {"id": 1, "label": "TaskOne"}
        assert records[1]["id"] == 2
        assert records[1]["task"] == ["A", "B"]

    def test_replace_and_query_records(self, sqlite_path, sample_errors):
        """测试全量覆盖写入以及分页、筛选、排序查询。"""
        replace_records(sqlite_path, sample_errors)

        total, total_pages, page_items = query_records(
            sqlite_path,
            page=1,
            page_size=2,
            node="",
            keyword="task",
            sort_order="newest",
        )
        assert total == 2
        assert total_pages == 1
        assert [item["event_id"] for item in page_items] == [3, 1]

        total, total_pages, page_items = query_records(
            sqlite_path,
            page=1,
            page_size=10,
            node="s2",
            keyword="boom",
            sort_order="oldest",
        )
        assert total == 1
        assert total_pages == 1
        assert page_items[0]["event_id"] == 2
        assert page_items[0]["task"] == ["A", "B"]

    def test_append_and_load_records_by_event_ids(self, sqlite_path, sample_errors):
        """测试追加写入以及按 event_id 定位读取。"""
        replace_records(sqlite_path, sample_errors[:2])

        assert get_event_ids(sqlite_path) == [1]

        appended = append_records(sqlite_path, sample_errors[2:])
        assert appended == 2
        assert get_event_ids(sqlite_path) == [1, 2, 3]

        selected = load_records_by_event_ids(sqlite_path, [3, 1])
        assert [item["event_id"] for item in selected] == [1, 3]

    def test_promote_record_to_failed_by_event_id(self, sqlite_path, sample_errors):
        """测试按 event_id 更新记录状态与错误信息。"""
        waiting_record = {
            "event_id": 9,
            "stage": "s9",
            "status": "waiting",
            "task": {"value": 9},
        }
        replace_records(sqlite_path, [waiting_record])

        conn = connect_db(sqlite_path)
        try:
            updated = promote_record_to_failed_by_event_id(
                conn,
                9,
                19,
                error_ts=9.5,
                error_type="RuntimeError",
                error_message="boom",
            )
            conn.commit()
        finally:
            conn.close()

        assert updated is True
        failed_records = load_records(sqlite_path, "failed")
        assert len(failed_records) == 1
        assert failed_records[0]["event_id"] == 19
        assert failed_records[0]["status"] == "failed"
        assert failed_records[0]["error_ts"] == 9.5
        assert failed_records[0]["error_type"] == "RuntimeError"
        assert failed_records[0]["error_message"] == "boom"

    def test_update_record_event_id_by_event_id(self, sqlite_path):
        """测试按 event_id 迁移记录的 event_id。"""
        waiting_record = {
            "event_id": 9,
            "stage": "s9",
            "status": "pending",
            "task": {"value": 9},
        }
        replace_records(sqlite_path, [waiting_record])

        conn = connect_db(sqlite_path)
        try:
            updated = update_record_event_id_by_event_id(conn, 9, 99)
            conn.commit()
        finally:
            conn.close()

        assert updated is True
        pending_records = load_records(sqlite_path, "pending")
        assert len(pending_records) == 1
        assert pending_records[0]["event_id"] == 99
        assert pending_records[0]["status"] == "pending"
        assert pending_records[0]["error_type"] == ""
        assert pending_records[0]["error_message"] == ""

    def test_delete_record_by_event_id(self, sqlite_path, sample_errors):
        """测试按 event_id 删除记录。"""
        replace_records(sqlite_path, sample_errors[1:])

        conn = connect_db(sqlite_path)
        try:
            deleted = delete_record_by_event_id(conn, 2)
            conn.commit()
        finally:
            conn.close()

        assert deleted is True
        assert [item["event_id"] for item in load_records(sqlite_path)] == [1, 3]

    def test_load_task_records_and_grouping(self, sqlite_path, sample_errors):
        """测试任务-错误配对读取以及按 stage 聚合。"""
        replace_records(sqlite_path, sample_errors)

        pairs = load_task_records(sqlite_path)
        assert len(pairs) == 3
        assert pairs[0][0] == {"id": 1, "label": "TaskOne"}
        assert pairs[0][1].error_type == "ValueError"
        assert pairs[1][0] == ["A", "B"]
        assert str(pairs[1][1]) == "RuntimeError(boom happened)"
