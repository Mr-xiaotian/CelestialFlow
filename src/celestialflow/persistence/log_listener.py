from multiprocessing import Queue as MPQueue
from queue import Empty
from threading import Thread
from time import localtime, strftime

from loguru import logger as loguru_logger

from ..task_types import TerminationSignal, TERMINATION_SIGNAL

# 日志级别字典
LEVEL_DICT = {
    "TRACE": 0,
    "DEBUG": 10,
    "SUCCESS": 20,
    "INFO": 30,
    "WARNING": 40,
    "ERROR": 50,
    "CRITICAL": 60,
}


class LogListener:
    """
    日志监听进程，用于将日志写入文件
    """

    def __init__(self):
        now = strftime("%Y-%m-%d", localtime())
        self.log_path = f"logs/log_sinker({now}).log"
        self.log_queue = MPQueue()
        self._thread = None

    def start(self):
        loguru_logger.remove()
        loguru_logger.add(
            self.log_path,
            level="TRACE",
            format="{time:YYYY-MM-DD HH:mm:ss} {level} {message}",
            enqueue=True,
        )
        if self._thread is None or not self._thread.is_alive():
            self._thread = Thread(target=self._listen, daemon=True)
            self._thread.start()
        # self.log_queue.put({"level": "DEBUG", "message": "[Listener] Started."})

    def _listen(self):
        while True:
            try:
                record = self.log_queue.get(timeout=0.5)
                if isinstance(record, TerminationSignal):
                    break
                loguru_logger.log(record["level"], record["message"])
            except Empty:
                continue
            # except Exception as e:
            #     loguru_logger.error(f"[Listener] thread error: {type(e).__name__}({e})")

    def get_queue(self):
        return self.log_queue

    def stop(self):
        if self._thread is None:
            return

        self.log_queue.put(TERMINATION_SIGNAL)
        self._thread.join()
        self._thread = None
        # self.log_queue.put({"level": "DEBUG", "message": "[Listener] Stopped."})
