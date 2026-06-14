import sqlite3

from celestialflow.persistence.core_fallback import FallbackInlet, FallbackSpout
from tests.conftest import wait_until


class TestFailPersistence:
    def test_fail_persistence(self, tmp_path, monkeypatch):
        """`FallbackInlet`/`FallbackSpout` 应将 fallback 记录持久化到 sqlite。"""
        monkeypatch.chdir(tmp_path)

        spout = FallbackSpout(error_source='test_source')
        inlet = FallbackInlet(spout.get_queue())

        spout.start()
        try:
            inlet.task_fallback('s1', err_id=1, error=ValueError('oops'), task='data1')
            inlet.task_fallback('s1', err_id=2, error=RuntimeError('fail'), task='data2')
            wait_until(
                lambda: spout.total_fallback_num == 2,
                message='timeout waiting for fallback_spout to process records',
            )
        finally:
            spout.stop()

        assert spout.total_fallback_num == 2
        assert spout.db_path is not None
        assert spout.db_path.exists()
        assert spout.db_path.suffix == ".sqlite3"

        pairs = spout.get_fallback_pairs()
        assert len(pairs) == 2
        assert pairs[0][0] == 'data1'
        assert pairs[0][1].error_type == 'ValueError'
        assert pairs[1][0] == 'data2'
        assert pairs[1][1].error_type == 'RuntimeError'

        conn = sqlite3.connect(spout.db_path)
        try:
            rows = conn.execute(
                "SELECT event_id, status, task_json FROM records ORDER BY id ASC"
            ).fetchall()
        finally:
            conn.close()

        assert rows == [
            (1, "failed", '"data1"'),
            (2, "failed", '"data2"'),
        ]
