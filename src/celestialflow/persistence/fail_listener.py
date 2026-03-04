import os
from datetime import datetime
from multiprocessing import Queue as MPQueue
from queue import Empty
from threading import Lock, Thread

from ..task_types import TerminationSignal, TERMINATION_SIGNAL
from .tools import append_jsonl_log, cleanup_mpqueue


class FailListener:
    def __init__(self, error_source: str):
        self.error_source = error_source
        self.fail_queue = MPQueue()
        self._thread = None
        self.fallback_path = ""
        self.total_error_num = 0
        self._counter_lock = Lock()

    def start(self):
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S-%f")[:-3]
        self.fallback_path = f"./fallback/{date_str}/{self.error_source}({time_str}).jsonl"
        self.total_error_num = 0

        if self._thread is None or not self._thread.is_alive():
            self._thread = Thread(target=self._listen, daemon=True)
            self._thread.start()

    def _listen(self):
        while True:
            try:
                record = self.fail_queue.get(timeout=0.5)
                if isinstance(record, TerminationSignal):
                    break
                append_jsonl_log(record, self.fallback_path)
                if isinstance(record, dict) and record.get("error_id") is not None:
                    with self._counter_lock:
                        self.total_error_num += 1
            except Empty:
                continue

    def get_queue(self):
        return self.fail_queue

    def get_fallback_path(self) -> str:
        return os.path.abspath(self.fallback_path)

    def stop(self):
        if self._thread is None:
            return

        self.fail_queue.put(TERMINATION_SIGNAL)
        self._thread.join()
        self._thread = None
        cleanup_mpqueue(self.fail_queue)
