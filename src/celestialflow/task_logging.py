from multiprocessing import Queue as MPQueue
from queue import Empty
from threading import Thread
from time import localtime, strftime
from typing import List

from loguru import logger as loguru_logger

from .task_types import TerminationSignal, TERMINATION_SIGNAL


class LogListener:
    """
    日志监听进程，用于将日志写入文件
    """

    def __init__(self, level="INFO"):
        now = strftime("%Y-%m-%d", localtime())
        self.log_path = f"logs/task_logger({now}).log"
        self.level = level
        self.log_queue = MPQueue()
        self._thread = Thread(target=self._listen, daemon=True)

    def start(self):
        # 配置 loguru 的两个 handler，stdout + file
        loguru_logger.remove()
        loguru_logger.add(
            self.log_path,
            level=self.level,
            format="{time:YYYY-MM-DD HH:mm:ss} {level} {message}",
            enqueue=True,
        )
        self._thread.start()
        loguru_logger.debug("LogListener started.")

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
            #     loguru_logger.error(f"LogListener thread error: {type(e).__name__}({e})")

    def get_queue(self):
        return self.log_queue

    def stop(self):
        self.log_queue.put(TERMINATION_SIGNAL)
        self._thread.join()
        loguru_logger.debug("LogListener stopped.")


class TaskLogger:
    """
    多进程安全日志包装类，所有日志通过队列发送到监听进程写入
    """

    def __init__(self, log_queue=None):
        self.log_queue: MPQueue = log_queue

    def _log(self, level: str, message: str):
        self.log_queue.put({"level": level.upper(), "message": message})

    # ==== manager ====
    def start_manager(self, func_name, task_num, execution_mode, worker_limit):
        text = f"'{func_name}' start {task_num} tasks by {execution_mode}"
        text += f"({worker_limit} workers)." if execution_mode != "serial" else "."
        self._log("INFO", text)

    def end_manager(
        self,
        func_name,
        execution_mode,
        use_time,
        success_num,
        failed_num,
        duplicated_num,
    ):
        self._log(
            "INFO",
            f"'{func_name}' end tasks by {execution_mode}. Use {use_time:.2f} second. "
            f"{success_num} tasks successed, {failed_num} tasks failed, {duplicated_num} tasks duplicated.",
        )

    # ==== stage ====
    def start_stage(self, stage_name, func_name, execution_mode, worker_limit):
        text = f"The {stage_name} in '{func_name}' start tasks by {execution_mode}"
        text += f"({worker_limit} workers)." if execution_mode != "serial" else "."
        self._log("INFO", text)

    def end_stage(
        self,
        stage_name,
        func_name,
        execution_mode,
        use_time,
        success_num,
        failed_num,
        duplicated_num,
    ):
        self._log(
            "INFO",
            f"The {stage_name} in '{func_name}' end tasks by {execution_mode}. Use {use_time:.2f} second. "
            f"{success_num} tasks successed, {failed_num} tasks failed, {duplicated_num} tasks duplicated.",
        )

    # ==== layer ====
    def start_layer(self, layer: List[str], layer_level: int):
        self._log("INFO", f"Layer {layer} start. Layer level: {layer_level}.")

    def end_layer(self, layer: List[str], use_time: float):
        self._log("INFO", f"Layer {layer} end. Use {use_time:.2f} second.")

    # ==== graph ====
    def start_graph(self, stage_structure):
        self._log("INFO", f"Starting TaskGraph stages. Graph structure:")
        for line in stage_structure:
            self._log("INFO", line)

    def end_graph(self, use_time):
        self._log("INFO", f"TaskGraph end. Use {use_time:.2f} second.")

    # ==== task ====
    def task_success(self, func_name, task_info, execution_mode, result_info, use_time):
        self._log(
            "SUCCESS",
            f"In '{func_name}', Task {task_info} completed by {execution_mode}. Result is {result_info}. Used {use_time:.2f} seconds.",
        )

    def task_retry(self, func_name, task_info, retry_times, exception):
        self._log(
            "WARNING",
            f"In '{func_name}', Task {task_info} failed {retry_times} times and will retry: ({type(exception).__name__}).",
        )

    def task_error(self, func_name, task_info, exception):
        exception_text = str(exception).replace("\n", " ")
        self._log(
            "ERROR",
            f"In '{func_name}', Task {task_info} failed and can't retry: ({type(exception).__name__}){exception_text}.",
        )

    def task_duplicate(self, func_name, task_info):
        self._log("SUCCESS", f"In '{func_name}', Task {task_info} has been duplicated.")

    # ==== splitter task ====
    def splitter_success(self, func_name, task_info, split_count, use_time):
        self._log(
            "SUCCESS",
            f"In '{func_name}', Task {task_info} has split into {split_count} parts. Used {use_time:.2f} seconds.",
        )
