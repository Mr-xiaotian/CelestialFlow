from celestialflow.persistence.core_fail import FailInlet, FailSpout
from tests.conftest import wait_until


class TestFailPersistence:
    def test_fail_persistence(self, tmp_path, monkeypatch):
        """`FailInlet`/`FailSpout` 应将错误记录持久化到 JSONL。"""
        monkeypatch.chdir(tmp_path)

        spout = FailSpout(error_source='test_source')
        inlet = FailInlet(spout.get_queue())

        spout.start()
        try:
            inlet.start_graph([{'node': 's1'}])
            inlet.task_error('s1', err_id=1, error=ValueError('oops'), task='data1')
            inlet.task_error('s1', err_id=2, error=RuntimeError('fail'), task='data2')
            wait_until(
                lambda: spout.total_error_num == 2,
                message='timeout waiting for fail_spout to process records',
            )
        finally:
            spout.stop()

        assert spout.total_error_num == 2
        assert spout.jsonl_path.exists()

        pairs = spout.get_error_pairs()
        assert len(pairs) == 2
        assert pairs[0][0] == 'data1'
        assert pairs[0][1].error_type == 'ValueError'
        assert pairs[1][0] == 'data2'
        assert pairs[1][1].error_type == 'RuntimeError'

        raw_records = [line for line in spout.jsonl_path.read_text(encoding="utf-8").splitlines() if '"error_id"' in line]
        assert '"task": "data1"' in raw_records[0]
        assert '"task": "data2"' in raw_records[1]
