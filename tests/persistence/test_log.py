from celestialflow.persistence.core_log import LogInlet, LogSpout
from conftest import wait_until


class TestLogPersistence:
    def test_log_persistence(self, tmp_path, monkeypatch):
        """`LogInlet`/`LogSpout` 应将日志批量刷新到文件。"""
        monkeypatch.chdir(tmp_path)

        spout = LogSpout()
        inlet = LogInlet(log_level='INFO').bind_spout(spout)

        spout.start()
        try:
            inlet.graph_start("test_graph", "thread", ['test message'])
            inlet.task_retry("func", "hello world", 1, ValueError("oops"), 0)
            inlet.graph_end("test_graph", 1.0)
            inlet.node_start('stage', 1, 'parallel-4')
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

    def test_skip_log(self, tmp_path, monkeypatch):
        """`LogInlet.task_skip` 应在 INFO 级别写入跳过日志。"""
        monkeypatch.chdir(tmp_path)

        spout = LogSpout()
        inlet = LogInlet(log_level='INFO').bind_spout(spout)

        spout.start()
        try:
            inlet.task_skip("stage", "hello world", 7, 8)
            wait_until(
                lambda: spout.log_path.exists()
                and 'hello world' in spout.log_path.read_text(encoding='utf-8'),
                message='timeout waiting for log_spout to write skip record',
            )
        finally:
            spout.stop()

        content = spout.log_path.read_text(encoding='utf-8')
        assert 'hello world' in content
        assert 'skipped' in content
        assert '[7->8*]' in content
        assert 'INFO' in content
