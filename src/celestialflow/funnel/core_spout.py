# funnel/core_spout.py
from __future__ import annotations

from queue import Empty, Queue
from threading import Thread
from typing import Any

from ..runtime.util_errors import CelestialFlowError
from ..runtime.util_types import TERMINATION_SIGNAL, TerminationSignal


class BaseSpout:
    """数据监听器基类，在独立后台线程中消费队列记录。"""

    def __init__(self) -> None:
        """初始化监听器及其内部队列和线程引用。"""
        self.queue: Queue[Any] = Queue()
        self._thread: Thread | None = None

    def _before_start(self) -> None:
        """在后台线程启动前调用，子类可覆写以做初始化（如打开文件、清空缓存）。"""
        return None

    def _handle_record(self, record: Any) -> None:
        """
        处理单条队列记录，子类必须覆写。

        :param record: 队列中取出的记录
        """
        raise CelestialFlowError("_handle_record must be implemented by subclasses")

    def _after_stop(self) -> None:
        """在后台线程停止后调用，子类可覆写以做清理（如关闭文件句柄）。"""
        return None

    def start(self) -> None:
        """启动后台监听线程（若未运行）。"""
        self._before_start()
        if self._thread is None or not self._thread.is_alive():
            self._thread = Thread(target=self._spout, daemon=True)
            self._thread.start()

    def _spout(self) -> None:
        """后台线程主循环，持续从队列拉取记录并调用 _handle_record，收到终止信号时退出。"""
        while True:
            try:
                record = self.queue.get(timeout=0.5)
                if isinstance(record, TerminationSignal):
                    break
                self._handle_record(record)
            except Empty:
                continue

    def get_queue(self) -> Queue[Any]:
        """获取监听器的输入队列。"""
        return self.queue

    def stop(self) -> None:
        """发送终止信号并等待后台线程结束。"""
        if self._thread is None:
            return

        self.queue.put(TERMINATION_SIGNAL)
        self._thread.join()
        self._thread = None
        self._after_stop()
