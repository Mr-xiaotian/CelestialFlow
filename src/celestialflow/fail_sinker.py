import time, os
from multiprocessing import Queue as MPQueue
from queue import Empty
from threading import Thread
from time import localtime, strftime
from collections.abc import Iterable
from datetime import datetime

from .task_errors import LogLevelError
from .task_tools import append_jsonl_log, append_jsonl_logs, format_repr, cleanup_mpqueue
from .task_types import TerminationSignal, TERMINATION_SIGNAL


class FailListener:
    def __init__(self):
        self.fail_queue = MPQueue()
        self._thread = None

    def start(self, error_source="graph_errors"):
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S-%f")[:-3]
        self.fallback_path = f"./fallback/{date_str}/{error_source}({time_str}).jsonl"

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


class FailSinker:

    def __init__(self, fail_queue):
        self.fail_queue: MPQueue = fail_queue
        self.total_error_num = 0

    def _sink(self, record: dict):
        self.fail_queue.put(record)
        self.total_error_num += 1

    def start_graph(self, structure_json):
        """
        在运行开始时写入任务结构元信息到 jsonl 文件
        """
        meta_item = {
            "timestamp": datetime.now().isoformat(),
            "structure": structure_json,
        }
        self._sink(meta_item)

    def task_error(self, ts, stage_tag, error, err_id, task):
        """
        写入错误日志到 jsonl 文件中

        :param ts: 错误时间戳
        :param stage_tag: 阶段标签
        :param error: 错误信息
        :param err_id: 错误ID
        :param task: 任务字符串
        """
        error_message = f"{type(error).__name__}({error})"
        fail_item =  {
                "timestamp": datetime.fromtimestamp(ts).isoformat(),
                "stage": stage_tag,
                "error_repr": format_repr(error_message, 100),
                "task_repr": format_repr(task, 100),
                "error": error_message,
                "task": task,
                "error_id": err_id,
                "ts": ts,
            }
        self._sink(fail_item)
