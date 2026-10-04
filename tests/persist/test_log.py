from conftest import wait_until

from celestialflow.observer import (
    GraphEndEvent,
    GraphStartEvent,
    NodeStartEvent,
    TaskRetryEvent,
    TaskSkipEvent,
)
from celestialflow.persist.core_log import LogInlet, LogSpout
from celestialflow.reporter import MetricsObserver


class TestLogPersistence:
    def test_log_persistence(self, tmp_path, monkeypatch):
        """`LogInlet`/`LogSpout` 应将日志批量刷新到文件。"""
        monkeypatch.chdir(tmp_path)

        spout = LogSpout()
        inlet = LogInlet(MetricsObserver(), log_level='INFO').bind_spout(spout)

        spout.start()
        try:
            inlet.on_graph_start(
                GraphStartEvent(
                    graph="test_graph",
                    graph_mode="thread",
                    start_time=1.0,
                    class_name="TaskGraph",
                    is_dag=True,
                    nodes=["node"],
                    edges={"node": []},
                    source_nodes=["node"],
                    node_meta={
                        "node": {
                            "class_name": "TaskExecutor",
                            "execution_mode": "serial",
                            "max_workers": 1,
                        }
                    },
                    structure_list=["test message"],
                )
            )
            inlet.on_task_retry(
                TaskRetryEvent("func", None, "hello world", ValueError("oops"), 0, 1)
            )
            inlet.on_graph_end(GraphEndEvent("test_graph", 1.0))
            inlet.on_node_start(
                NodeStartEvent('node', 'parallel', 4)
            )
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
        """`LogInlet.on_task_skip` 应在 SUCCESS 级别写入跳过日志。"""
        monkeypatch.chdir(tmp_path)

        spout = LogSpout()
        inlet = LogInlet(MetricsObserver(), log_level='SUCCESS').bind_spout(spout)

        spout.start()
        try:
            inlet.on_task_skip(
                TaskSkipEvent("node", "hello world", "hello world", 7, 8)
            )
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
        assert 'SUCCESS' in content
