import sqlite3

from celestialflow.persistence.core_lifecycle import LifecycleInlet, LifecycleSpout


class TestLifecyclePersistence:
    def test_lifecycle_persistence(self, tmp_path, monkeypatch):
        """`LifecycleInlet`/`LifecycleSpout` 应按生命周期维护 sqlite 记录。"""
        monkeypatch.chdir(tmp_path)

        spout = LifecycleSpout()
        inlet = LifecycleInlet().bind_spout(spout)

        spout.start()
        try:
            inlet.task_input("s1", event_id=1, task="data1")
            inlet.task_fail(event_id=1, error_id=21, error=ValueError("oops"))

            inlet.task_input("s2", event_id=2, task="data2")
            inlet.task_success(event_id=2, result="ok2")

            inlet.task_input("s3", event_id=3, task="data3")
            inlet.task_duplicate(event_id=3)
        finally:
            spout.stop()

        assert spout.db_path is not None
        assert spout.db_path.exists()
        assert spout.db_path.suffix == ".sqlite3"

        pairs = spout.get_task_error_pairs("s1")
        assert len(pairs) == 1
        assert pairs[0][0] == "data1"
        assert pairs[0][1] == ("ValueError", "oops")

        conn = sqlite3.connect(spout.db_path)
        try:
            rows = conn.execute(
                """
                SELECT event_id, ts, stage, status, error_type, error_message, task_json, result_json
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
            inlet.task_input("s1", event_id=1, task="task1")
            inlet.task_success(event_id=1, result=100)
            inlet.task_input("s2", event_id=2, task="task2")
            inlet.task_success(event_id=2, result=200)
        finally:
            spout.stop()

        pairs = spout.get_task_result_pairs("s1")
        assert pairs == [("task1", 100)]

    def test_retry_persistence(self, tmp_path, monkeypatch):
        """重试应更新 pending 记录的重试次数，最终晋升时保留该信息。"""
        monkeypatch.chdir(tmp_path)
        spout = LifecycleSpout()
        inlet = LifecycleInlet().bind_spout(spout)

        spout.start()
        try:
            # 重试后最终成功：错误信息应在晋升 success 时清空
            inlet.task_input("s1", event_id=1, task="retry_ok")
            inlet.task_retry(event_id=1, retry_times=1, error=ValueError("try 1"))
            inlet.task_retry(event_id=1, retry_times=2, error=ValueError("try 2"))
            inlet.task_success(event_id=1, result="ok")

            # 重试后最终失败：保留最新错误信息
            inlet.task_input("s2", event_id=2, task="retry_fail")
            inlet.task_retry(event_id=2, retry_times=1, error=ValueError("try 1"))
            inlet.task_retry(event_id=2, retry_times=2, error=ValueError("try 2"))
            inlet.task_fail(event_id=2, error_id=22, error=ValueError("final boom"))
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
                stage TEXT NOT NULL,
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
