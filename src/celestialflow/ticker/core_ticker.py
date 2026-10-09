# ticker/core_ticker.py
from __future__ import annotations

import time
from threading import Condition, Thread

from ..runtime.util_errors import ConfigurationError, RuntimeStateError
from .core_event import TickEvent
from .core_handler import TickHandler, validate_tick_period

_JOIN_TIMEOUT: float = 5.0
"""停止节拍器时等待后台线程退出的最大秒数。"""


class Ticker:
    """基于时间驱动的节拍器。

    在独立后台线程中以固定速率触发节拍：以 ``time.monotonic()`` 为基准锚定计划
    触发时刻，每拍构造 :class:`~celestialflow.ticker.core_event.TickEvent` 并交由
    :class:`~celestialflow.ticker.core_handler.TickHandler` 处理。若某拍处理耗时
    超过周期，则跳过错过的节拍（计入 :attr:`~celestialflow.ticker.core_event.TickEvent.skipped`），
    不做追赶，避免请求风暴。首拍在启动后经过一个周期才触发。

    处理器在本线程内联顺序执行，因此慢处理器会推迟后续节拍；需要异步解耦时可把
    处理器实现为写入队列、由独立消费者处理的形态。节拍器本身不依赖 ``funnel``，
    两者可在使用处按需组合。

    失败隔离分两层：处理器
    :meth:`~celestialflow.ticker.core_handler.TickHandler.on_tick` 抛出的异常交由
    该处理器自身的
    :meth:`~celestialflow.ticker.core_handler.TickHandler.handle_exception` 处理；
    若其再抛出，则异常向上传播。根处理器通常为
    :class:`~celestialflow.ticker.core_hub.TickHub`，此时逃逸的异常会被本循环捕获
    并回调该 hub 的 ``handle_exception`` 兜底，节拍循环不会因此退出。若根处理器
    不是 TickHub 且其 ``handle_exception`` 亦抛出异常，则该异常会终止后台线程。
    """

    def __init__(
        self,
        interval: float,
        handler: TickHandler,
        *,
        name: str = "ticker",
    ) -> None:
        """
        初始化节拍器。

        :param interval: 基准周期（秒），必须为正数
        :param handler: 节拍处理器，通常为
            :class:`~celestialflow.ticker.core_hub.TickHub`
        :param name: 后台线程名称，默认 ``"ticker"``
        :raises ConfigurationError: ``interval`` 非正，或处理器 ``tick_period`` 非法
        """
        if interval <= 0:
            raise ConfigurationError(
                f"ticker interval must be positive, got {interval}"
            )
        validate_tick_period(handler)

        self._handler = handler
        self._name = name

        self._cond = Condition()
        self._interval = float(interval)
        self._stopped = False
        self._thread: Thread | None = None

    # ==== 生命周期 ====

    def start(self) -> None:
        """启动后台节拍线程（若未运行）。"""
        self._before_start()
        if self._thread is None or not self._thread.is_alive():
            with self._cond:
                self._stopped = False
            self._thread = Thread(target=self._run, name=self._name, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """
        停止后台节拍线程并等待其结束。

        :raises RuntimeStateError: 线程未能在超时时间内退出
        """
        if self._thread is None:
            return

        with self._cond:
            self._stopped = True
            self._cond.notify_all()

        if self._thread.is_alive():
            self._thread.join(timeout=_JOIN_TIMEOUT)
        if self._thread.is_alive():
            raise RuntimeStateError(
                f"Ticker thread did not terminate within {_JOIN_TIMEOUT:g} seconds."
            )

        self._thread = None
        self._after_stop()

    def is_running(self) -> bool:
        """
        判断后台节拍线程是否正在运行。

        :return: 线程存活时为 ``True``
        :rtype: bool
        """
        return self._thread is not None and self._thread.is_alive()

    # ==== 调速 ====

    def get_interval(self) -> float:
        """
        读取当前基准周期。

        :return: 当前周期（秒）
        :rtype: float
        """
        with self._cond:
            return self._interval

    def set_interval(self, interval: float) -> None:
        """
        动态调整基准周期，下一拍起生效并重新锚定计划时刻。

        :param interval: 新的基准周期（秒），必须为正数
        :raises ConfigurationError: ``interval`` 非正
        """
        if interval <= 0:
            raise ConfigurationError(
                f"ticker interval must be positive, got {interval}"
            )
        with self._cond:
            self._interval = float(interval)
            self._cond.notify_all()

    # ==== 循环 ====

    def _run(self) -> None:
        """后台线程主循环：按固定速率触发节拍并分发。"""
        seq = 0
        prev_fire = time.monotonic()
        interval = self.get_interval()

        while True:
            with self._cond:
                if self._stopped:
                    return

                interval = self._interval
                next_deadline = prev_fire + interval
                timeout = next_deadline - time.monotonic()
                if timeout > 0:
                    self._cond.wait(timeout)
                if self._stopped:
                    return

                # 被 ``set_interval`` 唤醒或虚假唤醒时，若尚未到点则重新等待。
                interval = self._interval
                if time.monotonic() < prev_fire + interval:
                    continue

            fired = time.monotonic()
            scheduled = prev_fire + interval
            lateness = fired - scheduled
            skipped = int(lateness // interval) if lateness > 0 else 0
            prev_fire = scheduled + skipped * interval
            seq += 1

            event = TickEvent(
                seq=seq,
                interval=interval,
                scheduled_at=scheduled,
                fired_at=fired,
                wall_time=time.time(),
                drift=fired - scheduled,
                skipped=skipped,
            )
            self._dispatch(event)

    def _dispatch(self, event: TickEvent) -> None:
        """
        将节拍分发给处理器，并隔离处理器抛出的异常。

        :param event: 当前节拍事件
        """
        handler = self._handler
        if not handler.should_tick(event):
            return
        try:
            handler.on_tick(event)
        except Exception as e:
            handler.handle_exception(e)

    # ==== 生命周期回调 ====

    def _before_start(self) -> None:
        """在后台线程启动前调用，子类可覆写以做初始化。"""
        return None

    def _after_stop(self) -> None:
        """在后台线程停止后调用，子类可覆写以做清理。"""
        return None
