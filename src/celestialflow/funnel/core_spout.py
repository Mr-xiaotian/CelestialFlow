# funnel/core_spout.py
from __future__ import annotations

from multiprocessing import Queue as MPQueue
from queue import Empty
from threading import Thread
from typing import Any

from ..runtime.util_queue import cleanup_mpqueue
from ..runtime.util_types import TERMINATION_SIGNAL, TerminationSignal


class BaseSpout:
    """数据监听器基类，在独立后台线程中消费队列记录。"""

    def __init__(self) -> None:
        """初始化监听器及其内部队列和线程引用。"""
        self.queue: Any = MPQueue()
        self._thread: Thread | None = None

    def _before_start(self) -> None:
        return None

    def _handle_record(self, record: Any) -> None:
        raise NotImplementedError

    def _after_stop(self) -> None:
        return None

    def start(self) -> None:
        """启动后台监听线程（若未运行）。"""
        self._before_start()
        if self._thread is None or not self._thread.is_alive():
            self._thread = Thread(target=self._spout, daemon=True)
            self._thread.start()

    def _spout(self) -> None:
        while True:
            try:
                record = self.queue.get(timeout=0.5)
                if isinstance(record, TerminationSignal):
                    break
                self._handle_record(record)
            except Empty:
                continue
            except Exception:  # ← 新增：防止线程崩溃
                continue  # 或记录到 stderr，至少不丢后续记录

    def get_queue(self) -> MPQueue:
        """获取监听器的输入队列。"""
        return self.queue

    def stop(self) -> None:
        """发送终止信号并等待后台线程结束。"""
        if self._thread is None:
            return

        self.queue.put(TERMINATION_SIGNAL)
        self._thread.join()
        self._thread = None
        cleanup_mpqueue(self.queue)
        self._after_stop()
