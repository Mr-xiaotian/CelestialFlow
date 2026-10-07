from pathlib import Path

import pytest

from celestialflow.assembly import core_run
from celestialflow.assembly.core_run import run_graph_resources, run_node_resources
from celestialflow.observer import MetricsObserver, ObserverHub
from celestialflow.persist.core_lifecycle import LifecycleSpout
from celestialflow.persist.core_log import LogInlet, LogSpout
from celestialflow.reporter import PushSpout
from celestialflow.ticker import Ticker


class _InjectionTarget:
    """满足图入口注入目标参数要求的最简替身。"""

    def inject_tasks(self, tasks) -> None:
        """忽略注入任务。"""
        return None

    def inject_terminations(self, nodes) -> None:
        """忽略注入终止符。"""
        return None


def _patch_recording_spouts(monkeypatch, stopped: list[str]) -> None:
    """将上下文引用的 spout 替换为记录 ``stop`` 调用的子类。"""

    class _RecordingLifecycleSpout(LifecycleSpout):
        def stop(self) -> None:
            super().stop()
            stopped.append('lifecycle')

    class _RecordingLogSpout(LogSpout):
        def stop(self) -> None:
            super().stop()
            stopped.append('log')

    monkeypatch.setattr(core_run, 'LifecycleSpout', _RecordingLifecycleSpout)
    monkeypatch.setattr(core_run, 'LogSpout', _RecordingLogSpout)


def _patch_recording_push_spouts(monkeypatch, used: list[str]) -> None:
    """将图入口引用的推送 spout 替换为记录构造函数调用的子类。"""

    class _RecordingPushSpout(PushSpout):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            used.append('push')

    monkeypatch.setattr(core_run, 'PushSpout', _RecordingPushSpout)


def _patch_recording_ticker(monkeypatch, events: list[str]) -> None:
    """将图入口引用的 ticker 替换为记录启停调用的子类。"""

    class _RecordingTicker(Ticker):
        def start(self) -> None:
            super().start()
            events.append('ticker-start')

        def stop(self) -> None:
            super().stop()
            events.append('ticker-stop')

    monkeypatch.setattr(core_run, 'Ticker', _RecordingTicker)


class TestGraphRunResources:
    def test_yields_db_path_and_registers_observers(self, tmp_path, monkeypatch):
        """图入口进入时应启动 spout、产出数据库路径并注入 lifecycle / log inlet。"""
        monkeypatch.chdir(tmp_path)
        observers = ObserverHub()

        with run_graph_resources(observers, MetricsObserver(), _InjectionTarget()) as db_path:
            assert db_path is not None
            assert Path(db_path).exists()
            # 默认不启用上报，仅 lifecycle / log 两个全局 inlet。
            assert len(observers._snapshot()) == 2

    def test_stops_spouts_on_exit(self, tmp_path, monkeypatch):
        """图入口退出时应停止 lifecycle / log spout。"""
        monkeypatch.chdir(tmp_path)
        stopped: list[str] = []
        _patch_recording_spouts(monkeypatch, stopped)

        with run_graph_resources(ObserverHub(), MetricsObserver(), _InjectionTarget()):
            pass

        assert set(stopped) == {'lifecycle', 'log'}

    def test_cleans_up_when_body_raises(self, tmp_path, monkeypatch):
        """图入口上下文体内抛出异常时，异常应向外传播且 spout 仍被回收。"""
        monkeypatch.chdir(tmp_path)
        stopped: list[str] = []
        _patch_recording_spouts(monkeypatch, stopped)

        with pytest.raises(RuntimeError, match='boom'):
            with run_graph_resources(ObserverHub(), MetricsObserver(), _InjectionTarget()):
                raise RuntimeError('boom')

        assert set(stopped) == {'lifecycle', 'log'}

    def test_uses_push_spout_when_if_report_enabled(self, tmp_path, monkeypatch):
        """``if_report`` 为真且配置了 ``report_url`` 时图入口使用 ``PushSpout``。"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'pyproject.toml').write_text(
            '[tool.celestialflow]\n'
            'if_report = true\n'
            'report_url = "http://127.0.0.1:9000"\n',
            encoding='utf-8',
        )
        used: list[str] = []
        _patch_recording_push_spouts(monkeypatch, used)

        with run_graph_resources(ObserverHub(), MetricsObserver(), _InjectionTarget()):
            pass

        assert used == ['push']

    def test_no_push_spout_when_if_report_disabled(self, tmp_path, monkeypatch):
        """``if_report`` 为假时图入口不创建任何推送通道（即使配置了 ``report_url``）。"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'pyproject.toml').write_text(
            '[tool.celestialflow]\n'
            'if_report = false\n'
            'report_url = "http://127.0.0.1:9000"\n',
            encoding='utf-8',
        )
        used: list[str] = []
        _patch_recording_push_spouts(monkeypatch, used)

        with run_graph_resources(ObserverHub(), MetricsObserver(), _InjectionTarget()):
            pass

        assert used == []

    def test_uses_default_url_when_if_report_enabled_without_url(
        self, tmp_path, monkeypatch
    ):
        """``if_report`` 为真但未配置 ``report_url`` 时，用默认地址构建 ``PushSpout``。"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'pyproject.toml').write_text(
            '[tool.celestialflow]\nif_report = true\n', encoding='utf-8'
        )
        used: list[str] = []
        _patch_recording_push_spouts(monkeypatch, used)

        with run_graph_resources(ObserverHub(), MetricsObserver(), _InjectionTarget()):
            pass

        assert used == ['push']

    def test_starts_and_stops_snapshot_ticker_when_report_enabled(
        self, tmp_path, monkeypatch
    ):
        """启用上报时应启动快照节拍器，并在退出时停止。"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'pyproject.toml').write_text(
            '[tool.celestialflow]\n'
            'if_report = true\n'
            'report_url = "http://127.0.0.1:9000"\n',
            encoding='utf-8',
        )
        events: list[str] = []
        _patch_recording_push_spouts(monkeypatch, events)
        _patch_recording_ticker(monkeypatch, events)

        with run_graph_resources(ObserverHub(), MetricsObserver(), _InjectionTarget()):
            pass

        assert events == ['push', 'ticker-start', 'ticker-stop']


class TestNodeRunResources:
    def test_registers_metrics_and_inlets(self, tmp_path, monkeypatch):
        """节点入口应内部创建指标观察者，并注入 lifecycle / log inlet。"""
        monkeypatch.chdir(tmp_path)
        observers = ObserverHub()

        with run_node_resources(observers) as db_path:
            assert db_path is not None
            snapshot = observers._snapshot()
            # 指标观察者 + lifecycle + log
            assert len(snapshot) == 3
            assert any(isinstance(observer, MetricsObserver) for observer in snapshot)

    def test_log_level_from_pyproject(self, tmp_path, monkeypatch):
        """``LogInlet`` 的日志级别应从项目级 ``pyproject.toml`` 读取。"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'pyproject.toml').write_text(
            '[tool.celestialflow]\nlog_level = "ERROR"\n', encoding='utf-8'
        )
        observers = ObserverHub()

        with run_node_resources(observers):
            inlets = [
                observer
                for observer in observers._snapshot()
                if isinstance(observer, LogInlet)
            ]
            assert len(inlets) == 1
            assert inlets[0].log_level == 'ERROR'

    def test_stops_spouts_on_exit(self, tmp_path, monkeypatch):
        """节点入口退出时应停止 lifecycle / log spout。"""
        monkeypatch.chdir(tmp_path)
        stopped: list[str] = []
        _patch_recording_spouts(monkeypatch, stopped)

        with run_node_resources(ObserverHub()):
            pass

        assert set(stopped) == {'lifecycle', 'log'}
