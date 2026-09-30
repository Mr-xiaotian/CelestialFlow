from pathlib import Path

import pytest

from celestialflow.observer import ObserverHub
from celestialflow.persist import core_run
from celestialflow.persist.core_lifecycle import LifecycleSpout
from celestialflow.persist.core_log import LogInlet, LogSpout
from celestialflow.persist.core_run import run_resources
from celestialflow.reporter import NullPushSpout, PushSpout


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
    """将上下文引用的推送 spout 替换为记录构造函数选择的子类。"""

    class _RecordingPushSpout(PushSpout):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            used.append('push')

    class _RecordingNullPushSpout(NullPushSpout):
        def __init__(self) -> None:
            super().__init__()
            used.append('null')

    monkeypatch.setattr(core_run, 'PushSpout', _RecordingPushSpout)
    monkeypatch.setattr(core_run, 'NullPushSpout', _RecordingNullPushSpout)


class TestLifecycleRunResources:
    def test_yields_db_path_and_registers_observers(self, tmp_path, monkeypatch):
        """进入上下文应启动 spout、产出数据库路径并注入全局观察者。"""
        monkeypatch.chdir(tmp_path)
        observers = ObserverHub()

        with run_resources(observers, "session-1") as db_path:
            assert db_path is not None
            assert Path(db_path).exists()
            # lifecycle / log / error 三个全局 inlet。
            assert len(observers._snapshot()) == 3

    def test_stops_spouts_on_exit(self, tmp_path, monkeypatch):
        """退出上下文应停止两个 spout。"""
        monkeypatch.chdir(tmp_path)
        stopped: list[str] = []
        _patch_recording_spouts(monkeypatch, stopped)

        with run_resources(ObserverHub(), "session-1"):
            pass

        assert set(stopped) == {'lifecycle', 'log'}

    def test_log_level_from_pyproject(self, tmp_path, monkeypatch):
        """``LogInlet`` 的日志级别应从项目级 ``pyproject.toml`` 读取。"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'pyproject.toml').write_text(
            '[tool.celestialflow]\nlog_level = "ERROR"\n', encoding='utf-8'
        )
        observers = ObserverHub()

        with run_resources(observers, "session-1"):
            inlets = [
                observer
                for observer in observers._snapshot()
                if isinstance(observer, LogInlet)
            ]
            assert len(inlets) == 1
            assert inlets[0].log_level == 'ERROR'

    def test_cleans_up_when_body_raises(self, tmp_path, monkeypatch):
        """上下文体内抛出异常时，异常应向外传播且 spout 仍被回收。"""
        monkeypatch.chdir(tmp_path)
        stopped: list[str] = []
        _patch_recording_spouts(monkeypatch, stopped)

        with pytest.raises(RuntimeError, match='boom'):
            with run_resources(ObserverHub(), 'session-1'):
                raise RuntimeError('boom')

        assert set(stopped) == {'lifecycle', 'log'}

    def test_uses_push_spout_when_if_report_enabled(self, tmp_path, monkeypatch):
        """``if_report`` 为真且配置了 ``report_url`` 时使用 ``PushSpout``。"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'pyproject.toml').write_text(
            '[tool.celestialflow]\n'
            'if_report = true\n'
            'report_url = "http://127.0.0.1:9000"\n',
            encoding='utf-8',
        )
        used: list[str] = []
        _patch_recording_push_spouts(monkeypatch, used)

        with run_resources(ObserverHub(), 'session-1'):
            pass

        assert used == ['push']

    def test_uses_null_push_spout_when_if_report_disabled(self, tmp_path, monkeypatch):
        """``if_report`` 为假时不用 ``PushSpout``（即使配置了 ``report_url``）。"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'pyproject.toml').write_text(
            '[tool.celestialflow]\n'
            'if_report = false\n'
            'report_url = "http://127.0.0.1:9000"\n',
            encoding='utf-8',
        )
        used: list[str] = []
        _patch_recording_push_spouts(monkeypatch, used)

        with run_resources(ObserverHub(), 'session-1'):
            pass

        assert used == ['null']

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

        with run_resources(ObserverHub(), 'session-1'):
            pass

        assert used == ['push']
