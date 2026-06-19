# funnel/core_spout.py
from __future__ import annotations

import traceback
from queue import Empty, Queue
from threading import Thread
from typing import Any

from ..runtime.util_errors import CelestialFlowError
from ..runtime.util_types import TERMINATION_SIGNAL, TerminationSignal
from .util_count import PendingCounter


class BaseSpout:
    """数据监听器基类，在独立后台线程中消费队列记录。"""

    def __init__(self) -> None:
        """初始化监听器及其内部队列、待处理计数器和线程引用。"""
        self._queue: Queue[Any] = Queue()
        self._counter = PendingCounter()
        self._thread: Thread | None = None

    # ==== 外部调用函数 ====

    def start(self) -> None:
        """启动后台监听线程（若未运行）。"""
        self._before_start()
        if self._thread is None or not self._thread.is_alive():
            self._thread = Thread(target=self._spout, daemon=True)
            self._thread.start()

    def _spout(self) -> None:
        """
        后台线程主循环。

        持续从队列拉取记录并调用 ``_handle_record()``，收到终止信号时退出。
        待处理数量在记录处理完成后递减，因此统计口径包含“已出队但仍在处理”的记录。
        """
        while True:
            try:
                record = self._queue.get(timeout=0.5)
            except Empty:
                continue

            if isinstance(record, TerminationSignal):
                break

            try:
                self._handle_record(record)
            except Exception:
                # 单条记录处理失败不致死线程。
                traceback.print_exc()
            finally:
                self._counter.decrement()

    def stop(self) -> None:
        """发送终止信号并等待后台线程结束。"""
        if self._thread is None:
            return

        self._queue.put(TERMINATION_SIGNAL)
        if self._thread.is_alive():
            self._thread.join(timeout=5)

        self._thread = None
        self._after_stop()

    def get_queue(self) -> Queue[Any]:
        """获取监听器的输入队列。"""
        return self._queue

    def get_counter(self) -> PendingCounter:
        """
        获取与当前监听器绑定的待处理计数器。

        :return: 待处理计数器
        :rtype: PendingCounter
        """
        return self._counter

    def get_pending_count(self) -> int:
        """
        读取当前仍未处理完成的记录数量。

        :return: 当前待处理数量
        :rtype: int
        """
        return self._counter.get_count()

    # ==== 生命周期回调 ====

    def _before_start(self) -> None:
        """在后台线程启动前调用，子类可覆写以做初始化（如打开文件、清空缓存）。"""
        return None

    def _handle_record(self, _record: Any) -> None:
        """
        处理单条队列记录，子类必须覆写。

        :param _record: 队列中取出的记录
        """
        raise CelestialFlowError("_handle_record must be implemented by subclasses")

    def _after_stop(self) -> None:
        """在后台线程停止后调用，子类可覆写以做清理（如关闭文件句柄）。"""
        return None
