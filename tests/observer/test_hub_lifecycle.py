from __future__ import annotations

import pytest

from celestialflow.observer import Observer, ObserverHub


class LifecycleObserver(Observer):
    """记录启停调用并可选择性失败的观察者。"""

    def __init__(
        self,
        log: list[str],
        name: str,
        *,
        fail_on_start: bool = False,
        fail_on_stop: bool = False,
    ) -> None:
        self._log = log
        self._name = name
        self._fail_on_start = fail_on_start
        self._fail_on_stop = fail_on_stop

    def start(self) -> None:
        """记录启动或抛出预设异常。"""
        if self._fail_on_start:
            raise RuntimeError(f"{self._name} start")
        self._log.append(f"start:{self._name}")

    def stop(self) -> None:
        """记录停止或抛出预设异常。"""
        if self._fail_on_stop:
            raise RuntimeError(f"{self._name} stop")
        self._log.append(f"stop:{self._name}")


def test_base_observer_start_stop_are_noop() -> None:
    """基类的 ``start`` / ``stop`` 默认不持有资源，可直接调用。"""
    observer = Observer()

    observer.start()
    observer.stop()


def test_hub_starts_in_order_and_stops_in_reverse() -> None:
    """hub 应按注册顺序启动，按逆序停止。"""
    log: list[str] = []
    hub = ObserverHub()
    hub.add_observer(LifecycleObserver(log, "a"))
    hub.add_observer(LifecycleObserver(log, "b"))

    hub.start()
    assert log == ["start:a", "start:b"]

    log.clear()
    hub.stop()
    assert log == ["stop:b", "stop:a"]


def test_hub_rolls_back_started_observers_on_start_failure() -> None:
    """启动失败时逆序回滚已启动的观察者，不再启动后续观察者。"""
    log: list[str] = []
    hub = ObserverHub()
    hub.add_observer(LifecycleObserver(log, "a"))
    hub.add_observer(LifecycleObserver(log, "b", fail_on_start=True))
    hub.add_observer(LifecycleObserver(log, "c"))

    with pytest.raises(RuntimeError, match="b start"):
        hub.start()

    assert log == ["start:a", "stop:a"]


def test_hub_stop_aggregates_failures_and_keeps_stopping() -> None:
    """单个观察者停止失败不应中断其余观察者，异常最终聚合抛出。"""
    log: list[str] = []
    hub = ObserverHub()
    hub.add_observer(LifecycleObserver(log, "a"))
    hub.add_observer(LifecycleObserver(log, "b", fail_on_stop=True))

    with pytest.raises(ExceptionGroup):
        hub.stop()

    assert log == ["stop:a"]
