# persistence/core_base.py
from __future__ import annotations

from multiprocessing import Queue as MPQueue
from queue import Empty
from threading import Thread

from ..runtime.util_queue import cleanup_mpqueue
from ..runtime.util_types import TerminationSignal, TERMINATION_SIGNAL


class BaseListener:
    def __init__(self) -> None:
        self.queue = MPQueue()
        self._thread: Thread | None = None

    def _before_start(self) -> None:
        return None

    def _handle_record(self, record) -> None:
        raise NotImplementedError

    def _after_stop(self) -> None:
        return None

    def start(self) -> None:
        self._before_start()
        if self._thread is None or not self._thread.is_alive():
            self._thread = Thread(target=self._listen, daemon=True)
            self._thread.start()

    def _listen(self) -> None:
        while True:
            try:
                record = self.queue.get(timeout=0.5)
                if isinstance(record, TerminationSignal):
                    break
                self._handle_record(record)
            except Empty:
                continue

    def get_queue(self) -> MPQueue:
        return self.queue

    def stop(self) -> None:
        if self._thread is None:
            return

        self.queue.put(TERMINATION_SIGNAL)
        self._thread.join()
        self._thread = None
        cleanup_mpqueue(self.queue)
        self._after_stop()


class BaseSinker:
    def __init__(self, queue: MPQueue) -> None:
        self.queue: MPQueue = queue

    def _sink(self, record) -> None:
        self.queue.put(record)
