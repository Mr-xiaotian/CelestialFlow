import sqlite3

from celestialflow.persistence.core_fallback import FallbackInlet, FallbackSpout
from tests.conftest import wait_until


class TestFailPersistence:
    def test_fallback_lifecycle_persistence(self, tmp_path, monkeypatch):
        """`FallbackInlet`/`FallbackSpout` 应按生命周期维护 sqlite 记录。"""
        monkeypatch.chdir(tmp_path)

        spout = FallbackSpout(error_source='test_source')
        inlet = FallbackInlet(spout.get_queue())

        spout.start()
        try:
            inlet.task_in('s1', event_id=1, task='data1')
            inlet.task_retry(event_id=1, retry_id=11)
            inlet.task_fail('s1', event_id=11, error_id=21, error=ValueError('oops'))

            inlet.task_in('s2', event_id=2, task='data2')
            inlet.task_success(event_id=2, result='ok2')

            inlet.task_in('s3', event_id=3, task='data3')
            inlet.task_duplicate(event_id=3)
        finally:
            spout.stop()

        assert spout.db_path is not None
        assert spout.db_path.exists()
        assert spout.db_path.suffix == ".sqlite3"

        pairs = spout.get_task_error_pairs()
        assert len(pairs) == 1
        assert pairs[0][0] == 'data1'
        assert pairs[0][1] == ('ValueError', 'oops')

        conn = sqlite3.connect(spout.db_path)
        try:
            rows = conn.execute(
                """
                SELECT event_id, stage, status, error_type, error_message, task_json, result_json
                FROM records
                ORDER BY id ASC
                """
            ).fetchall()
        finally:
            conn.close()

        assert rows == [
            (21, "s1", "failed", "ValueError", "oops", '"data1"', 'null'),
            (2, "s2", "success", "", "", '"data2"', '"ok2"'),
        ]
