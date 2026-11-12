from conftest import wait_until

from celestialflow.observer import (
    GraphEndEvent,
    GraphStartEvent,
    NodeStartEvent,
    TaskRetryEvent,
    TaskSkipEvent,
)
from celestialflow.persist.core_log import LogObserver
from celestialflow.observer import MetricsObserver


class TestLogPersistence:
    def test_log_persistence(self, tmp_path, monkeypatch):
        """`LogObserver` 应将日志批量刷新到文件。"""
        monkeypatch.chdir(tmp_path)

        observer = LogObserver(MetricsObserver(), log_level='INFO')

        observer.start()
        try:
            observer.on_event(
                GraphStartEvent(
                    graph="test_graph",
                    graph_mode="thread",
                    start_time=1.0,
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
                )
            )
            observer.on_event(
                TaskRetryEvent("func", None, "hello world", ValueError("oops"), 0, 1)
            )
            observer.on_event(GraphEndEvent("test_graph", 2.0, 1.0))
            observer.on_event(
                NodeStartEvent('node', 'parallel', 4, 1.0)
            )
            wait_until(
                lambda: observer.log_path.exists()
                and '| node |' in observer.log_path.read_text(encoding='utf-8')
                and 'hello world' in observer.log_path.read_text(encoding='utf-8'),
                message='timeout waiting for LogObserver to write records',
            )
        finally:
            observer.stop()

        assert observer.log_path.exists()
        content = observer.log_path.read_text(encoding='utf-8')
        assert '| node |' in content
        assert 'hello world' in content
        assert 'INFO' in content
        assert 'WARNING' in content

    def test_skip_log(self, tmp_path, monkeypatch):
        """`LogObserver` 收到跳过事件时应在 SUCCESS 级别写入跳过日志。"""
        monkeypatch.chdir(tmp_path)

        observer = LogObserver(MetricsObserver(), log_level='SUCCESS')

        observer.start()
        try:
            observer.on_event(
                TaskSkipEvent("node", "hello world", "hello world", 7, 8)
            )
            wait_until(
                lambda: observer.log_path.exists()
                and 'hello world' in observer.log_path.read_text(encoding='utf-8'),
                message='timeout waiting for LogObserver to write skip record',
            )
        finally:
            observer.stop()

        content = observer.log_path.read_text(encoding='utf-8')
        assert 'hello world' in content
        assert 'skipped' in content
        assert '[7->8*]' in content
        assert 'SUCCESS' in content
