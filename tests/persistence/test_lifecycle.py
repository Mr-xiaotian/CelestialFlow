import sqlite3

from celestialflow.observability import (
    TaskFailEvent,
    TaskInputEvent,
    TaskRetryEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
)
from celestialflow.persistence.core_lifecycle import LifecycleInlet, LifecycleSpout
from celestialflow.persistence.util_sqlite import (
    load_task_error_records,
    load_task_result_records,
)


class TestLifecyclePersistence:
    def test_lifecycle_persistence(self, tmp_path, monkeypatch):
        """`LifecycleInlet`/`LifecycleSpout` 应按生命周期维护 sqlite 记录。"""
        monkeypatch.chdir(tmp_path)

        spout = LifecycleSpout()
        inlet = LifecycleInlet().bind_spout(spout)

        spout.start()
        try:
            inlet.on_task_input(
                TaskInputEvent("s1", "data1", "(data1)", 1, "external")
            )
            inlet.on_task_fail(
                TaskFailEvent(
                    "s1", "data1", "(data1)", ValueError("oops"), 1, 21
                )
            )

            inlet.on_task_input(
                TaskInputEvent("s2", "data2", "(data2)", 2, "external")
            )
            inlet.on_task_success(
                TaskSuccessEvent("s2", "data2", "(data2)", "ok2", "(ok2)", 0.0, 2, 3)
            )
        finally:
            spout.stop()

        assert spout.db_path is not None
        assert spout.db_path.exists()
        assert spout.db_path.suffix == ".sqlite3"

        pairs = load_task_error_records(spout.db_path, "s1")
        assert len(pairs) == 1
        assert pairs[0][0] == "data1"
        assert pairs[0][1] == ("ValueError", "oops")

        conn = sqlite3.connect(spout.db_path)
        try:
            rows = conn.execute(
                """
                SELECT event_id, ts, node, status, error_type, error_message, task_json, result_json
                FROM records
                ORDER BY id ASC
                """
            ).fetchall()
        finally:
            conn.close()

        assert [row[0] for row in rows] == [21, 2]
        assert [row[2:] for row in rows] == [
            ("s1", "failed", "ValueError", "oops", '"data1"', 'null'),
            ("s2", "success", "", "", '"data2"', '"ok2"'),
        ]
        assert rows[0][1] > 0
        assert rows[1][1] > 0

    def test_success_persistence(self, tmp_path, monkeypatch):
        """`LifecycleSpout` 应持久化 success 结果并可读回 task-result 对。"""
        monkeypatch.chdir(tmp_path)
        spout = LifecycleSpout()
        inlet = LifecycleInlet().bind_spout(spout)

        spout.start()
        try:
            inlet.on_task_input(
                TaskInputEvent("s1", "task1", "(task1)", 1, "external")
            )
            inlet.on_task_success(
                TaskSuccessEvent("s1", "task1", "(task1)", 100, "(100)", 0.0, 1, 2)
            )
            inlet.on_task_input(
                TaskInputEvent("s2", "task2", "(task2)", 2, "external")
            )
            inlet.on_task_success(
                TaskSuccessEvent("s2", "task2", "(task2)", 200, "(200)", 0.0, 2, 3)
            )
        finally:
            spout.stop()

        pairs = load_task_result_records(spout.db_path, "s1")
        assert pairs == [("task1", 100)]

    def test_retry_persistence(self, tmp_path, monkeypatch):
        """重试应更新 pending 记录的重试次数，最终晋升时保留该信息。"""
        monkeypatch.chdir(tmp_path)
        spout = LifecycleSpout()
        inlet = LifecycleInlet().bind_spout(spout)

        spout.start()
        try:
            # 重试后最终成功：错误信息应在晋升 success 时清空
            inlet.on_task_input(
                TaskInputEvent("s1", "retry_ok", "(retry_ok)", 1, "external")
            )
            inlet.on_task_retry(
                TaskRetryEvent("s1", "retry_ok", "(retry_ok)", ValueError("try 1"), 1, 1)
            )
            inlet.on_task_retry(
                TaskRetryEvent("s1", "retry_ok", "(retry_ok)", ValueError("try 2"), 1, 2)
            )
            inlet.on_task_success(
                TaskSuccessEvent(
                    "s1", "retry_ok", "(retry_ok)", "ok", "(ok)", 0.0, 1, 3
                )
            )

            # 重试后最终失败：保留最新错误信息
            inlet.on_task_input(
                TaskInputEvent("s2", "retry_fail", "(retry_fail)", 2, "external")
            )
            inlet.on_task_retry(
                TaskRetryEvent(
                    "s2", "retry_fail", "(retry_fail)", ValueError("try 1"), 2, 1
                )
            )
            inlet.on_task_retry(
                TaskRetryEvent(
                    "s2", "retry_fail", "(retry_fail)", ValueError("try 2"), 2, 2
                )
            )
            inlet.on_task_fail(
                TaskFailEvent(
                    "s2",
                    "retry_fail",
                    "(retry_fail)",
                    ValueError("final boom"),
                    2,
                    22,
                )
            )
        finally:
            spout.stop()

        assert spout.db_path is not None
        conn = sqlite3.connect(spout.db_path)
        try:
            rows = conn.execute(
                """
                SELECT event_id, status, error_type, error_message, task_json, result_json
                     , retry_times
                FROM records
                ORDER BY id ASC
                """
            ).fetchall()
        finally:
            conn.close()

        assert [(row[0], row[1], row[6]) for row in rows] == [
            (1, "success", 2),
            (22, "failed", 2),
        ]
        # 成功记录不携带错误信息，失败记录保留最终错误
        assert rows[0][2:6] == ("", "", '"retry_ok"', '"ok"')
        assert rows[1][2:6] == ("ValueError", "final boom", '"retry_fail"', "null")

    def test_skip_persistence(self, tmp_path, monkeypatch):
        """`LifecycleInlet.on_task_skip` 应将 pending 记录晋升为 skipped 并切换事件 ID。"""
        monkeypatch.chdir(tmp_path)
        spout = LifecycleSpout()
        inlet = LifecycleInlet().bind_spout(spout)

        spout.start()
        try:
            inlet.on_task_input(
                TaskInputEvent("s1", "skip_me", "(skip_me)", 1, "external")
            )
            inlet.on_task_skip(
                TaskSkipEvent("s1", "skip_me", "(skip_me)", 1, 31)
            )
            inlet.on_task_input(
                TaskInputEvent("s2", "run_me", "(run_me)", 2, "external")
            )
            inlet.on_task_success(
                TaskSuccessEvent("s2", "run_me", "(run_me)", "ok", "(ok)", 0.0, 2, 3)
            )
        finally:
            spout.stop()

        assert spout.db_path is not None
        conn = sqlite3.connect(spout.db_path)
        try:
            rows = conn.execute(
                """
                SELECT event_id, status, error_type, error_message, task_json, result_json
                FROM records
                ORDER BY id ASC
                """
            ).fetchall()
        finally:
            conn.close()

        assert [(row[0], row[1]) for row in rows] == [(31, "skipped"), (2, "success")]
        assert rows[0][2:6] == ("", "", '"skip_me"', "null")

    def test_old_db_gets_retry_times_column(self, tmp_path, monkeypatch):
        """旧库缺 retry_times 列时，`connect_db` 应自动 ALTER 补列。"""
        monkeypatch.chdir(tmp_path)
        db_path = tmp_path / "old.sqlite3"
        conn = sqlite3.connect(db_path)
        _ = conn.execute(
            """
            CREATE TABLE records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                ts REAL,
                node TEXT NOT NULL,
                status TEXT NOT NULL,
                error_type TEXT NOT NULL DEFAULT '',
                error_message TEXT NOT NULL DEFAULT '',
                task_json TEXT NOT NULL,
                result_json TEXT NOT NULL DEFAULT 'null'
            )
            """
        )
        conn.commit()
        conn.close()

        from celestialflow.persistence.util_sqlite import connect_db

        conn = connect_db(db_path)
        try:
            columns = [
                row[1]
                for row in conn.execute("PRAGMA table_info(records)").fetchall()
            ]
            assert "retry_times" in columns
        finally:
            conn.close()
