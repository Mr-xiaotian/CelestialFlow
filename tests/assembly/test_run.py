import pytest

from celestialflow.assembly import core_run
from celestialflow.assembly.core_run import (
    run_local_resources,
    run_reporting_resources,
)
from celestialflow.observer import MetricsObserver, ObserverHub
from celestialflow.persist.core_lifecycle import LifecycleObserver
from celestialflow.persist.core_log import LogObserver
from celestialflow.reporter import InjectionTicker, PushObserver, SnapshotTicker
from celestialflow.runtime.core_config import DEFAULT_REPORT_URL, ReportConfig
from celestialflow.runtime.util_errors import InvalidOptionError
from celestialflow.ticker import TickClock, Ticker, TickEvent, TickHub


class _InjectionTarget:
    """满足上报入口注入目标参数要求的最简替身。"""

    def inject_tasks(self, tasks) -> None:
        """忽略注入任务。"""
        return None

    def inject_terminations(self, nodes) -> None:
        """忽略注入终止符。"""
        return None


def _patch_recording_observers(monkeypatch, stopped: list[str]) -> None:
    """将上下文引用的持久化观察者替换为记录 ``stop`` 调用的子类。"""

    class _RecordingLifecycleObserver(LifecycleObserver):
        def stop(self) -> None:
            super().stop()
            stopped.append('lifecycle')

    class _RecordingLogObserver(LogObserver):
        def stop(self) -> None:
            super().stop()
            stopped.append('log')

    monkeypatch.setattr(core_run, 'LifecycleObserver', _RecordingLifecycleObserver)
    monkeypatch.setattr(core_run, 'LogObserver', _RecordingLogObserver)


def _patch_recording_push_observers(
    monkeypatch, used: list[str], urls: list[str] | None = None
) -> None:
    """将上报入口引用的推送观察者替换为记录构造与停止调用的子类。"""

    class _RecordingPushObserver(PushObserver):
        def __init__(self, session_id, base_url, metrics_view, timeout=3.0) -> None:
            super().__init__(session_id, base_url, metrics_view, timeout)
            used.append('push')
            if urls is not None:
                urls.append(base_url)

        def stop(self) -> None:
            super().stop()
            used.append('push-stop')

    monkeypatch.setattr(core_run, 'PushObserver', _RecordingPushObserver)


def _patch_recording_clock(monkeypatch, events: list[str]) -> None:
    """将节拍资源引用的时钟替换为记录启停调用的子类。"""

    class _RecordingClock(TickClock):
        def start(self) -> None:
            super().start()
            events.append('clock-start')

        def stop(self) -> None:
            super().stop()
            events.append('clock-stop')

    monkeypatch.setattr(core_run, 'TickClock', _RecordingClock)


class _LoggingTicker(Ticker):
    """启动/停止时写入共享日志的 ticker。"""

    def __init__(self, log: list[str], name: str) -> None:
        self._log = log
        self._name = name

    def start(self) -> None:
        self._log.append(f'{self._name}-start')

    def stop(self) -> None:
        self._log.append(f'{self._name}-stop')

    def on_tick(self, event: TickEvent) -> None:
        return None


class TestTickResources:
    def test_starts_tickers_before_clock_and_stops_in_reverse(self, monkeypatch):
        """应先启动 ticker 资源再起钟，退出时先停钟再停 ticker。"""
        events: list[str] = []
        hub = TickHub()
        hub.add_ticker(_LoggingTicker(events, 'ticker'))
        _patch_recording_clock(monkeypatch, events)

        with run_local_resources(ObserverHub(), hub):
            assert events == ['ticker-start', 'clock-start']

        assert events == ['ticker-start', 'clock-start', 'clock-stop', 'ticker-stop']

    def test_add_ticker_while_running_starts_it(self, monkeypatch):
        """运行期加入的 ticker 应立即就绪。"""
        events: list[str] = []
        hub = TickHub()
        _patch_recording_clock(monkeypatch, events)

        with run_local_resources(ObserverHub(), hub):
            hub.add_ticker(_LoggingTicker(events, 'late'))
            assert events == ['clock-start', 'late-start']

        assert events == ['clock-start', 'late-start', 'clock-stop', 'late-stop']


class TestReportingResources:
    def test_registers_observers(self, tmp_path, monkeypatch):
        """上报入口进入时应启动 spout 并注册全部观察者。"""
        monkeypatch.chdir(tmp_path)
        observers = ObserverHub()

        with run_reporting_resources(
            observers,
            TickHub(),
            _InjectionTarget(),
            report=ReportConfig(url='http://127.0.0.1:9000'),
        ):
            # 指标观察者 + lifecycle + log + PushObserver
            assert len(observers._snapshot()) == 4

    def test_registers_report_tickers(self, tmp_path, monkeypatch):
        """上报入口应把快照与注入 ticker 注册到传入的 hub。"""
        monkeypatch.chdir(tmp_path)
        tickers = TickHub()

        with run_reporting_resources(
            ObserverHub(),
            tickers,
            _InjectionTarget(),
            report=ReportConfig(url='http://127.0.0.1:9000'),
        ):
            assert isinstance(tickers.find(SnapshotTicker), SnapshotTicker)
            assert isinstance(tickers.find(InjectionTicker), InjectionTicker)

    def test_tick_resources_stop_before_observers(self, tmp_path, monkeypatch):
        """节拍资源应先于观察者停止，避免推送通道关闭后仍有快照入队。"""
        monkeypatch.chdir(tmp_path)
        events: list[str] = []
        _patch_recording_push_observers(monkeypatch, events)
        _patch_recording_clock(monkeypatch, events)
        tickers = TickHub()
        tickers.add_ticker(_LoggingTicker(events, 'ticker'))

        with run_reporting_resources(
            ObserverHub(),
            tickers,
            _InjectionTarget(),
            report=ReportConfig(url='http://127.0.0.1:9000'),
        ):
            pass

        assert events == [
            'push',
            'ticker-start',
            'clock-start',
            'clock-stop',
            'ticker-stop',
            'push-stop',
        ]

    def test_stops_persistence_on_exit(self, tmp_path, monkeypatch):
        """上报入口退出时应停止 lifecycle / log 持久化观察者。"""
        monkeypatch.chdir(tmp_path)
        stopped: list[str] = []
        _patch_recording_observers(monkeypatch, stopped)

        with run_reporting_resources(
            ObserverHub(),
            TickHub(),
            _InjectionTarget(),
            report=ReportConfig(url='http://127.0.0.1:9000'),
        ):
            pass

        assert set(stopped) == {'lifecycle', 'log'}

    def test_cleans_up_when_body_raises(self, tmp_path, monkeypatch):
        """上下文体内抛出异常时，异常应向外传播且持久化观察者仍被回收。"""
        monkeypatch.chdir(tmp_path)
        stopped: list[str] = []
        _patch_recording_observers(monkeypatch, stopped)

        with pytest.raises(RuntimeError, match='boom'):
            with run_reporting_resources(
                ObserverHub(),
                TickHub(),
                _InjectionTarget(),
                report=ReportConfig(url='http://127.0.0.1:9000'),
            ):
                raise RuntimeError('boom')

        assert set(stopped) == {'lifecycle', 'log'}

    def test_uses_report_url_for_push_observer(self, tmp_path, monkeypatch):
        """推送观察者应采用 ``ReportConfig`` 中给定的地址。"""
        monkeypatch.chdir(tmp_path)
        used: list[str] = []
        urls: list[str] = []
        _patch_recording_push_observers(monkeypatch, used, urls)

        with run_reporting_resources(
            ObserverHub(),
            TickHub(),
            _InjectionTarget(),
            report=ReportConfig(url='http://127.0.0.1:9000'),
        ):
            pass

        assert used == ['push', 'push-stop']
        assert urls == ['http://127.0.0.1:9000']

    def test_uses_default_url_when_report_has_no_url(self, tmp_path, monkeypatch):
        """``ReportConfig()`` 使用默认地址构建 ``PushObserver``。"""
        monkeypatch.chdir(tmp_path)
        urls: list[str] = []
        _patch_recording_push_observers(monkeypatch, [], urls)

        with run_reporting_resources(
            ObserverHub(),
            TickHub(),
            _InjectionTarget(),
            report=ReportConfig(),
        ):
            pass

        assert urls == [DEFAULT_REPORT_URL]

    def test_log_level_argument(self, tmp_path, monkeypatch):
        """上报入口应按 ``log_level`` 参数构造 ``LogObserver``，并规范化为大写。"""
        monkeypatch.chdir(tmp_path)
        observers = ObserverHub()

        with run_reporting_resources(
            observers,
            TickHub(),
            _InjectionTarget(),
            log_level='error',
            report=ReportConfig(url='http://127.0.0.1:9000'),
        ):
            log_observers = [
                observer
                for observer in observers._snapshot()
                if isinstance(observer, LogObserver)
            ]

        assert len(log_observers) == 1
        assert log_observers[0].log_level == 'ERROR'

    def test_rejects_invalid_log_level(self, tmp_path, monkeypatch):
        """非法 ``log_level`` 应在进入运行期资源时抛出 ``InvalidOptionError``。"""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(InvalidOptionError):
            with run_reporting_resources(
                ObserverHub(),
                TickHub(),
                _InjectionTarget(),
                log_level='VERBOSE',
                report=ReportConfig(url='http://127.0.0.1:9000'),
            ):
                pass


class TestLocalResources:
    def test_registers_metrics_and_persistence(self, tmp_path, monkeypatch):
        """本地入口应内部创建指标观察者，并注入 lifecycle / log 观察者。"""
        monkeypatch.chdir(tmp_path)
        observers = ObserverHub()

        with run_local_resources(observers, TickHub()):
            snapshot = observers._snapshot()
            # 指标观察者 + lifecycle + log
            assert len(snapshot) == 3
            assert any(isinstance(observer, MetricsObserver) for observer in snapshot)

    def test_log_level_argument(self, tmp_path, monkeypatch):
        """``LogObserver`` 的日志级别应来自 ``log_level`` 参数。"""
        monkeypatch.chdir(tmp_path)
        observers = ObserverHub()

        with run_local_resources(observers, TickHub(), log_level='error'):
            log_observers = [
                observer
                for observer in observers._snapshot()
                if isinstance(observer, LogObserver)
            ]
            assert len(log_observers) == 1
            assert log_observers[0].log_level == 'ERROR'

    def test_rejects_invalid_log_level(self, tmp_path, monkeypatch):
        """非法 ``log_level`` 应抛出 ``InvalidOptionError``。"""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(InvalidOptionError):
            with run_local_resources(ObserverHub(), TickHub(), log_level='VERBOSE'):
                pass

    def test_stops_persistence_on_exit(self, tmp_path, monkeypatch):
        """本地入口退出时应停止 lifecycle / log 持久化观察者。"""
        monkeypatch.chdir(tmp_path)
        stopped: list[str] = []
        _patch_recording_observers(monkeypatch, stopped)

        with run_local_resources(ObserverHub(), TickHub()):
            pass

        assert set(stopped) == {'lifecycle', 'log'}
