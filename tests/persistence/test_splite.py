import json

import pytest

from celestialflow.persistence.util_sqlite import (
    connect_errors_db,
    insert_error_record,
    load_error_records,
    load_task_by_stage,
    load_task_error_pairs,
    normalize_error_record,
    query_error_records,
    replace_error_records,
)


@pytest.fixture
def sample_errors():
    """创建一组用于 sqlite 错误工具测试的样本记录。"""
    return [
        {"timestamp": "meta-only", "graph_name": "demo"},
        {
            "ts": 1.0,
            "stage": "s1",
            "error_id": 1,
            "error_type": "ValueError",
            "error_message": "bad value",
            "task": {"id": 1, "label": "TaskOne"},
        },
        {
            "ts": 2.0,
            "stage": "s2",
            "error_id": 2,
            "error_type": "RuntimeError",
            "error_message": "boom happened",
            "task": ["A", "B"],
        },
        {
            "ts": 3.0,
            "stage": "s1",
            "error_id": 3,
            "error_type": "TypeError",
            "error_message": "wrong type",
            "task": "PlainTask",
        },
    ]


@pytest.fixture
def sqlite_path(tmp_path):
    """创建临时 sqlite 文件路径。"""
    return tmp_path / "errors.sqlite3"


class TestSpliteUtils:
    def test_connect_errors_db_creates_table_and_indices(self, sqlite_path):
        """测试建立连接时会自动创建 errors 表和必要索引。"""
        conn = connect_errors_db(sqlite_path)
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

        assert "errors" in table_names
        assert "idx_errors_ts" in index_names
        assert "idx_errors_stage_ts" in index_names
        assert "idx_errors_type_ts" in index_names
        assert "idx_errors_error_id" in index_names

    def test_normalize_error_record(self, sample_errors):
        """测试错误记录会被归一化为 sqlite 可写格式。"""
        assert normalize_error_record(sample_errors[0]) is None

        normalized = normalize_error_record(sample_errors[1])

        assert normalized is not None
        assert normalized["ts"] == 1.0
        assert normalized["stage"] == "s1"
        assert normalized["error_id"] == 1
        assert normalized["error_type"] == "ValueError"
        assert normalized["error_message"] == "bad value"
        assert json.loads(normalized["task_json"]) == {"id": 1, "label": "TaskOne"}

    def test_insert_and_load_error_records(self, sqlite_path, sample_errors):
        """测试单条插入会忽略元信息，并能正常读回错误记录。"""
        conn = connect_errors_db(sqlite_path)
        try:
            assert insert_error_record(conn, sample_errors[0]) is False
            assert insert_error_record(conn, sample_errors[1]) is True
            assert insert_error_record(conn, sample_errors[2]) is True
            conn.commit()
        finally:
            conn.close()

        records = load_error_records(sqlite_path)

        assert len(records) == 2
        assert records[0]["id"] == 1
        assert records[0]["task"] == {"id": 1, "label": "TaskOne"}
        assert records[1]["id"] == 2
        assert records[1]["task"] == ["A", "B"]

    def test_replace_and_query_error_records(self, sqlite_path, sample_errors):
        """测试全量覆盖写入以及分页、筛选、排序查询。"""
        replace_error_records(sqlite_path, sample_errors)

        total, total_pages, page_items = query_error_records(
            sqlite_path,
            page=1,
            page_size=2,
            node="",
            keyword="task",
            sort_order="newest",
        )
        assert total == 2
        assert total_pages == 1
        assert [item["error_id"] for item in page_items] == [3, 1]

        total, total_pages, page_items = query_error_records(
            sqlite_path,
            page=1,
            page_size=10,
            node="s2",
            keyword="boom",
            sort_order="oldest",
        )
        assert total == 1
        assert total_pages == 1
        assert page_items[0]["error_id"] == 2
        assert page_items[0]["task"] == ["A", "B"]

    def test_load_task_error_pairs_and_grouping(self, sqlite_path, sample_errors):
        """测试任务-错误配对读取以及按 stage 聚合。"""
        replace_error_records(sqlite_path, sample_errors)

        pairs = load_task_error_pairs(sqlite_path)
        assert len(pairs) == 3
        assert pairs[0][0] == {"id": 1, "label": "TaskOne"}
        assert pairs[0][1].error_type == "ValueError"
        assert pairs[1][0] == ["A", "B"]
        assert str(pairs[1][1]) == "RuntimeError(boom happened)"

        grouped_by_stage = load_task_by_stage(sqlite_path)
        assert grouped_by_stage["s1"] == [
            {"id": 1, "label": "TaskOne"},
            "PlainTask",
        ]
        assert grouped_by_stage["s2"] == [["A", "B"]]
