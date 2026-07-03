import json

import pytest

from celestialflow.persistence.util_sqlite import (
    append_records,
    clear_records,
    connect_db,
    delete_record_by_event_id,
    get_max_event_id_in_fail,
    insert_record,
    load_records,
    load_records_after_event_id_in_fail,
    load_task_error_records,
    load_task_result_records,
    normalize_record,
    query_error_type_counts,
    query_records,
    promote_record_to_failed_by_event_id,
    promote_record_to_success_by_event_id,
    update_record_event_id_by_event_id,
)


@pytest.fixture
def sample_errors():
    """创建一组用于 sqlite 错误工具测试的样本记录。"""
    return [
        {"timestamp": "meta-only", "graph_name": "demo"},
        {
            "ts": 1.0,
            "stage": "s1",
            "status": "failed",
            "event_id": 1,
            "error_type": "ValueError",
            "error_message": "bad value",
            "task_json": {"id": 1, "label": "TaskOne"},
        },
        {
            "ts": 2.0,
            "stage": "s2",
            "status": "failed",
            "event_id": 2,
            "error_type": "RuntimeError",
            "error_message": "boom happened",
            "task_json": ["A", "B"],
        },
        {
            "ts": 3.0,
            "stage": "s1",
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
            "stage",
            "status",
            "error_type",
            "error_message",
            "task_json",
            "result_json",
        ]
        assert any(row[1] == "result_json" for row in result_info)

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
        assert normalized["ts"] == 1.0
        assert json.loads(normalized["task_json"]) == {"id": 1, "label": "TaskOne"}

    def test_normalize_record_requires_stage_and_status(self):
        """测试业务记录必须显式提供 stage 与 status。"""
        with pytest.raises(KeyError, match="stage"):
            normalize_record({"event_id": 1, "status": "failed", "task_json": {}})

        with pytest.raises(KeyError, match="status"):
            normalize_record({"event_id": 1, "stage": "s1", "task_json": {}})

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
        assert records[0]["ts"] == 1.0
        assert records[0]["task_json"] == {"id": 1, "label": "TaskOne"}
        assert records[0]["result_json"] is None
        assert records[1]["id"] == 2
        assert records[1]["ts"] == 2.0
        assert records[1]["task_json"] == ["A", "B"]
        assert records[1]["result_json"] is None

    def test_append_and_query_records(self, sqlite_path, sample_errors):
        """测试追加写入以及分页、筛选、排序查询。"""
        appended = append_records(sqlite_path, sample_errors)
        assert appended == 3

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
        assert page_items[0]["task_json"] == ["A", "B"]

    def test_clear_records(self, sqlite_path, sample_errors):
        """测试直接清空 records 表。"""
        appended = append_records(sqlite_path, sample_errors[1:])
        assert appended == 3

        clear_records(sqlite_path)

        assert load_records(sqlite_path) == []

    def test_get_max_event_id_in_fail(self, sqlite_path):
        """测试只统计 failed 状态中的最大 event_id。"""
        append_records(
            sqlite_path,
            [
                {
                    "event_id": 5,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": {"value": 5},
                },
                {
                    "event_id": 9,
                    "stage": "s1",
                    "status": "success",
                    "task_json": {"value": 9},
                    "result_json": {"ok": True},
                },
                {
                    "event_id": 7,
                    "stage": "s2",
                    "status": "failed",
                    "task_json": {"value": 7},
                },
            ],
        )

        assert get_max_event_id_in_fail(sqlite_path) == 7

    def test_get_max_event_id_in_fail_returns_none_when_no_failed(self, sqlite_path):
        """测试没有 failed 记录时返回 None。"""
        append_records(
            sqlite_path,
            [
                {
                    "event_id": 9,
                    "stage": "s1",
                    "status": "success",
                    "task_json": {"value": 9},
                    "result_json": {"ok": True},
                }
            ],
        )

        assert get_max_event_id_in_fail(sqlite_path) is None

    def test_load_records_after_event_id_in_fail(self, sqlite_path):
        """测试按 failed 的 event_id 下界增量读取记录。"""
        appended = append_records(
            sqlite_path,
            [
                {
                    "event_id": 3,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": {"value": 3},
                },
                {
                    "event_id": 5,
                    "stage": "s2",
                    "status": "success",
                    "task_json": {"value": 5},
                    "result_json": {"ok": True},
                },
                {
                    "event_id": 7,
                    "stage": "s3",
                    "status": "failed",
                    "task_json": {"value": 7},
                },
            ],
        )

        assert appended == 3
        assert [
            item["event_id"]
            for item in load_records_after_event_id_in_fail(sqlite_path, 3)
        ] == [7]

    def test_query_error_type_counts(self, sqlite_path):
        """测试按错误类型聚合全部 failed 记录。"""
        appended = append_records(
            sqlite_path,
            [
                {
                    "event_id": 1,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": {"value": 1},
                    "error_type": "ValueError",
                },
                {
                    "event_id": 2,
                    "stage": "s2",
                    "status": "failed",
                    "task_json": {"value": 2},
                    "error_type": "TypeError",
                },
                {
                    "event_id": 3,
                    "stage": "s3",
                    "status": "failed",
                    "task_json": {"value": 3},
                    "error_type": "ValueError",
                },
                {
                    "event_id": 4,
                    "stage": "s1",
                    "status": "success",
                    "task_json": {"value": 4},
                    "result_json": {"ok": True},
                    "error_type": "IgnoredError",
                },
            ],
        )
        assert appended == 4

        assert query_error_type_counts(sqlite_path) == [
            {"error_type": "ValueError", "count": 2},
            {"error_type": "TypeError", "count": 1},
        ]

    def test_query_error_type_counts_filters_by_node(self, sqlite_path):
        """测试按节点过滤错误类型聚合结果。"""
        appended = append_records(
            sqlite_path,
            [
                {
                    "event_id": 1,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": {"value": 1},
                    "error_type": "ValueError",
                },
                {
                    "event_id": 2,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": {"value": 2},
                    "error_type": "TypeError",
                },
                {
                    "event_id": 3,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": {"value": 3},
                    "error_type": "TypeError",
                },
                {
                    "event_id": 4,
                    "stage": "s2",
                    "status": "failed",
                    "task_json": {"value": 4},
                    "error_type": "RuntimeError",
                },
            ],
        )
        assert appended == 4

        assert query_error_type_counts(sqlite_path, node="s1") == [
            {"error_type": "TypeError", "count": 2},
            {"error_type": "ValueError", "count": 1},
        ]

    def test_append_records_skips_duplicate_event_ids(self, sqlite_path, sample_errors):
        """测试追加写入会跳过已存在的 event_id，保证重复同步幂等。"""
        appended = append_records(sqlite_path, sample_errors[1:3])
        assert appended == 2

        appended = append_records(sqlite_path, [sample_errors[1], sample_errors[3]])

        assert appended == 1
        assert [item["event_id"] for item in load_records(sqlite_path)] == [1, 2, 3]

    def test_promote_record_to_failed_by_event_id(self, sqlite_path, sample_errors):
        """测试按 event_id 更新记录状态与错误信息。"""
        waiting_record = {
            "event_id": 9,
            "stage": "s9",
            "status": "waiting",
            "task_json": {"value": 9},
        }
        appended = append_records(sqlite_path, [waiting_record])
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
        failed_records = load_records(sqlite_path, "failed")
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
            "stage": "s8",
            "status": "pending",
            "task_json": {"value": 8},
        }
        appended = append_records(sqlite_path, [pending_record])
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
        success_records = load_records(sqlite_path, "success")
        assert len(success_records) == 1
        assert success_records[0]["event_id"] == 8
        assert success_records[0]["status"] == "success"
        assert success_records[0]["ts"] == 8.5
        assert success_records[0]["result_json"] == {"ok": True, "value": [1, 2, 3]}
        assert success_records[0]["task_json"] == {"value": 8}

    def test_update_record_event_id_by_event_id(self, sqlite_path):
        """测试按 event_id 迁移记录的 event_id。"""
        waiting_record = {
            "event_id": 9,
            "stage": "s9",
            "status": "pending",
            "task_json": {"value": 9},
        }
        appended = append_records(sqlite_path, [waiting_record])
        assert appended == 1

        conn = connect_db(sqlite_path)
        try:
            updated = update_record_event_id_by_event_id(conn, 9, 99, ts=99.5)
            conn.commit()
        finally:
            conn.close()

        assert updated is True
        pending_records = load_records(sqlite_path, "pending")
        assert len(pending_records) == 1
        assert pending_records[0]["event_id"] == 99
        assert pending_records[0]["status"] == "pending"
        assert pending_records[0]["ts"] == 99.5
        assert pending_records[0]["error_type"] == ""
        assert pending_records[0]["error_message"] == ""

    def test_delete_record_by_event_id(self, sqlite_path, sample_errors):
        """测试按 event_id 删除记录。"""
        appended = append_records(sqlite_path, sample_errors[1:])
        assert appended == 3

        conn = connect_db(sqlite_path)
        try:
            deleted = delete_record_by_event_id(conn, 2)
            conn.commit()
        finally:
            conn.close()

        assert deleted is True
        assert [item["event_id"] for item in load_records(sqlite_path)] == [1, 3]

    def test_load_task_error_records_and_grouping(self, sqlite_path, sample_errors):
        """测试任务-错误配对读取以及按 stage 聚合。"""
        appended = append_records(sqlite_path, sample_errors)
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
            "stage": "s8",
            "status": "pending",
            "task_json": {"value": 8},
        }
        appended = append_records(sqlite_path, [pending_record])
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
