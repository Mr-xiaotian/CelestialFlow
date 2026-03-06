# persistence/fail.py
import os
from datetime import datetime
from multiprocessing import Queue as MPQueue
from queue import Empty
from threading import Lock, Thread

from ..runtime.tools import cleanup_mpqueue
from ..runtime.types import TerminationSignal, TERMINATION_SIGNAL
from ..utils.format import format_repr
from .jsonl import append_jsonl_log


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
        self.fallback_path = (
            f"./fallback/{date_str}/{self.error_source}({time_str}).jsonl"
        )
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


class FailSinker:
    """
    多进程安全失败记录包装类，所有失败记录通过队列发送到监听进程写入
    """

    def __init__(self, fail_queue):
        self.fail_queue: MPQueue = fail_queue

    def _sink(self, record: dict):
        self.fail_queue.put(record)

    def start_graph(self, structure_json):
        """
        在运行开始时写入任务结构元信息到 jsonl 文件
        """
        meta_item = {
            "timestamp": datetime.now().isoformat(),
            "structure": structure_json,
        }
        self._sink(meta_item)

    def start_executor(self, executor_tag: str):
        """
        在运行开始时写入执行器元信息到 jsonl 文件
        """
        meta_item = {
            "timestamp": datetime.now().isoformat(),
            "executor": executor_tag,
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
        fail_item = {
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
