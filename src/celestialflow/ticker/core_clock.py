# ticker/core_clock.py
from __future__ import annotations

import time
import traceback
from threading import Condition, Thread

from ..runtime.util_errors import ConfigurationError, RuntimeStateError
from .core_event import TickEvent
from .core_ticker import Ticker

DEFAULT_TICK_INTERVAL: float = 1.0
"""默认基准周期（秒）。各 ticker 以 ``tick_period`` 缩放出实际周期。"""

_JOIN_TIMEOUT: float = 5.0
"""停止时钟时等待后台线程退出的最大秒数。"""


class TickClock:
    """时间驱动的节拍时钟，是节拍树唯一的时间源头。

    在独立后台线程中以固定速率触发节拍：以 ``time.monotonic()`` 为基准锚定计划
    触发时刻，每拍构造 :class:`~celestialflow.ticker.core_event.TickEvent` 并交给
    根 ticker（通常是 :class:`~celestialflow.ticker.core_hub.TickHub`）。首拍在启动
    后经过一个周期才触发。

    时钟不属于节拍树：它只负责产生时间，分发由根 ticker 及其嵌套 hub 完成。因此
    一个进程里可以同时存在多个时钟（如多个任务图各有一个），各自维护独立的
    :attr:`~celestialflow.ticker.core_event.TickEvent.seq`。

    若某拍处理耗时超过周期，则跳过错过的节拍，不做追赶，避免请求风暴。根 ticker
    在本线程内联顺序执行，因此慢 ticker 会推迟后续节拍；需要异步解耦时可把 ticker
    实现为写入队列、由独立消费者处理的形态。

    根 ticker 抛出的异常会由根自身的 ``handle_exception`` 处理（若根为 hub，则在其
    内部分发时已隔离）；兜底自身再抛出时，时钟会打印回溯并继续，不会因静默的线程
    死亡而永久停摆。
    """

    def __init__(
        self,
        interval: float,
        root: Ticker,
        *,
        name: str = "ticker",
    ) -> None:
        """
        初始化时钟。

        :param interval: 基准周期（秒），必须为正数
        :param root: 根 ticker，通常是一个含若干 ticker 的
            :class:`~celestialflow.ticker.core_hub.TickHub`
        :param name: 后台线程名称，默认 ``"ticker"``
        :raises ConfigurationError: ``interval`` 非正
        """
        if interval <= 0:
            raise ConfigurationError(
                f"ticker interval must be positive, got {interval}"
            )

        self._root = root
        self._name = name

        self._cond = Condition()
        self._interval = float(interval)
        self._stopped = False
        self._thread: Thread | None = None

    # ==== 生命周期 ====

    def start(self) -> None:
        """启动后台节拍线程（若未运行）。"""
        if self.is_running():
            return

        with self._cond:
            self._stopped = False
        thread = Thread(target=self._run, name=self._name, daemon=True)
        thread.start()
        self._thread = thread

    def stop(self) -> None:
        """停止后台节拍线程。

        :raises RuntimeStateError: 线程未能在超时时间内退出
        """
        thread = self._thread
        if thread is None:
            return

        with self._cond:
            self._stopped = True
            self._cond.notify_all()

        if thread.is_alive():
            thread.join(timeout=_JOIN_TIMEOUT)
        if thread.is_alive():
            raise RuntimeStateError(
                f"TickClock thread did not terminate within "
                f"{_JOIN_TIMEOUT:g} seconds."
            )
        self._thread = None

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

        各 ticker 的实际周期随之按
        :attr:`~celestialflow.ticker.core_ticker.Ticker.tick_period` 缩放。

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
        """后台线程主循环：按固定速率产生节拍并交给根 ticker。"""
        seq = 0
        prev_fire = time.monotonic()

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

            event = TickEvent(seq=seq, fired_at=fired, wall_time=time.time())
            if not self._root.should_tick(event):
                continue
            try:
                self._root.on_tick(event)
            except Exception as exception:
                try:
                    self._root.handle_exception(exception)
                except Exception as fallback:
                    # 最后一层保护：连兜底都抛出时也保持时钟存活，避免静默停摆。
                    traceback.print_exception(fallback)
