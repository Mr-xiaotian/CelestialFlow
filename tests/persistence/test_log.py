from celestialflow.persistence.core_log import LogInlet, LogSpout
from tests.conftest import wait_until


class TestLogPersistence:
    def test_log_persistence(self, tmp_path, monkeypatch):
        """`LogInlet`/`LogSpout` 应将日志批量刷新到文件。"""
        monkeypatch.chdir(tmp_path)

        spout = LogSpout()
        inlet = LogInlet(spout.get_queue(), log_level='INFO')

        spout.start()
        try:
            inlet.start_graph("test_graph", ['test message'])
            inlet.task_retry('func', 'hello world', 1, ValueError('oops'), 0, 1)
            inlet.end_graph("test_graph", 1.0)
            inlet.start_stage('stage', 'normal', 'parallel-4')
            wait_until(
                lambda: spout.log_path.exists()
                and 'test message' in spout.log_path.read_text(encoding='utf-8')
                and 'hello world' in spout.log_path.read_text(encoding='utf-8'),
                message='timeout waiting for log_spout to write records',
            )
        finally:
            spout.stop()

        assert spout.log_path.exists()
        content = spout.log_path.read_text(encoding='utf-8')
        assert 'test message' in content
        assert 'hello world' in content
        assert 'INFO' in content
        assert 'WARNING' in content
