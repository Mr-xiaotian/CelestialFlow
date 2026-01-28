from multiprocessing import Queue as MPQueue
from queue import Empty
from threading import Thread
from time import localtime, strftime
from typing import List

from loguru import logger as loguru_logger

from .task_types import TerminationSignal, TERMINATION_SIGNAL


# 日志级别字典
LEVEL_DICT = {
    "TRACE": 0,
    "DEBUG": 10,
    "SUCCESS": 20,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


class LogListener:
    """
    日志监听进程，用于将日志写入文件
    """

    def __init__(self, level="INFO"):
        now = strftime("%Y-%m-%d", localtime())
        self.log_path = f"logs/task_logger({now}).log"
        self.level = level.upper()
        self.log_queue = MPQueue()
        self._thread = Thread(target=self._listen, daemon=True)

        if self.level not in LEVEL_DICT:
            raise ValueError(f"Invalid log level: {self.level}")

    def start(self):
        loguru_logger.remove()
        loguru_logger.add(
            self.log_path,
            level=self.level,
            format="{time:YYYY-MM-DD HH:mm:ss} {level} {message}",
            enqueue=True,
        )
        self._thread.start()
        loguru_logger.debug("[Listener] Started.")

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
        self.log_queue.put(TERMINATION_SIGNAL)
        self._thread.join()
        loguru_logger.debug("[Listener] Stopped.")


class TaskLogger:
    """
    多进程安全日志包装类，所有日志通过队列发送到监听进程写入
    """

    def __init__(self, log_queue, log_level="INFO"):
        self.log_queue: MPQueue = log_queue
        self.log_level: str = log_level.upper()

        if self.log_level not in LEVEL_DICT:
            raise ValueError(f"Invalid log level: {self.log_level}")

    def _log(self, level: str, message: str):
        level_upper = level.upper()
        if level_upper not in LEVEL_DICT:
            return
        if LEVEL_DICT[level_upper] < LEVEL_DICT[self.log_level]:
            return
        self.log_queue.put({"level": level_upper, "message": message})

    # ==== manager ====
    def start_manager(self, func_name, task_num, execution_mode_desc):
        text = (
            f"'Manager[{func_name}]' start {task_num} tasks by {execution_mode_desc}."
        )
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
            f"'Manager[{func_name}]' end tasks by {execution_mode}. Use {use_time:.2f} second. "
            f"{success_num} tasks successed, {failed_num} tasks failed, {duplicated_num} tasks duplicated.",
        )

    # ==== stage ====
    def start_stage(self, stage_tag, execution_mode, worker_limit):
        text = f"'{stage_tag}' start tasks by {execution_mode}"
        text += f"({worker_limit} workers)." if execution_mode != "serial" else "."
        self._log("INFO", text)

    def end_stage(
        self,
        stage_tag,
        execution_mode,
        use_time,
        success_num,
        failed_num,
        duplicated_num,
    ):
        self._log(
            "INFO",
            f"'{stage_tag}' end tasks by {execution_mode}. Use {use_time:.2f} second. "
            f"{success_num} tasks successed, {failed_num} tasks failed, {duplicated_num} tasks duplicated.",
        )

    # ==== layer ====
    def start_layer(self, layer: List[str], layer_level: int):
        self._log("INFO", f"Layer {layer} start. Layer level: {layer_level}.")

    def end_layer(self, layer: List[str], use_time: float):
        self._log("INFO", f"Layer {layer} end. Use {use_time:.2f} second.")

    # ==== graph ====
    def start_graph(self, stage_structure):
        self._log("INFO", f"Starting TaskGraph. Graph structure:")
        for line in stage_structure:
            self._log("INFO", line)

    def end_graph(self, use_time):
        self._log("INFO", f"TaskGraph end. Use {use_time:.2f} second.")

    # ==== task ====
    def task_input(self, func_name, task_info, source, input_id):
        self._log(
            "DEBUG",
            f"In '{func_name}', Task {task_info} input into {source}. [{input_id}*]",
        )

    def task_success(
        self,
        func_name,
        task_info,
        execution_mode,
        result_info,
        use_time,
        parent_id,
        success_id,
    ):
        self._log(
            "SUCCESS",
            f"In '{func_name}', Task {task_info} completed by {execution_mode}. Result is {result_info}. Used {use_time:.2f} seconds. [{parent_id}->{success_id}*]",
        )

    def task_retry(
        self, func_name, task_info, retry_times, exception, parent_id, retry_id
    ):
        self._log(
            "WARNING",
            f"In '{func_name}', Task {task_info} failed {retry_times} times and will retry: ({type(exception).__name__}). [{parent_id}->{retry_id}*]",
        )

    def task_error(self, func_name, task_info, exception, parent_id, error_id):
        exception_text = str(exception).replace("\n", " ")
        self._log(
            "ERROR",
            f"In '{func_name}', Task {task_info} failed and can't retry: ({type(exception).__name__}){exception_text}. [{parent_id}->{error_id}*]",
        )

    def task_duplicate(self, func_name, task_info, parent_id, duplicate_id):
        self._log(
            "SUCCESS",
            f"In '{func_name}', Task {task_info} has been duplicated. [{parent_id}->{duplicate_id}*]",
        )

    # ==== splitter ====
    def split_trace(self, func_name, part_index, part_total, parent_id, split_id):
        self._log(
            "TRACE",
            f"In '{func_name}', Task split part {part_index}/{part_total}. [{parent_id}->{split_id}*]",
        )

    def split_success(self, func_name, task_info, split_count, use_time):
        self._log(
            "SUCCESS",
            f"In '{func_name}', Task {task_info} has split into {split_count} parts. Used {use_time:.2f} seconds.",
        )

    # ==== router ====
    def route_success(
        self, func_name, task_info, target_node, use_time, parent_id, route_id
    ):
        self._log(
            "SUCCESS",
            f"In '{func_name}', Task {task_info} has routed to {target_node}. Used {use_time:.2f} seconds. [{parent_id}->{route_id}*]",
        )

    # ==== queue ====
    def put_item(self, item_type, item_id, queue_tag, stage_tag, direction):
        left, right = (
            (queue_tag, stage_tag) if direction == "in" else (stage_tag, queue_tag)
        )
        edge = f"'{left}' -> '{right}'"
        self._log("TRACE", f"Put {item_type}#{item_id} into Edge({edge}).")

    def put_item_error(self, queue_tag, stage_tag, direction, exception):
        left, right = (
            (queue_tag, stage_tag) if direction == "in" else (stage_tag, queue_tag)
        )
        edge = f"'{left}' -> '{right}'"
        exception_text = str(exception).replace("\n", " ")
        self._log(
            "WARNING",
            f"Put into Edge({edge}): ({type(exception).__name__}){exception_text}.",
        )

    def get_item(self, item_type, item_id, queue_tag, stage_tag, direction="in"):
        left, right = (
            (queue_tag, stage_tag) if direction == "in" else (stage_tag, queue_tag)
        )
        edge = f"'{left}' -> '{right}'"
        self._log("TRACE", f"Get {item_type}#{item_id} from Edge({edge}).")

    def get_item_error(
        self, queue_tag, stage_tag, direction="in", *, exception: Exception
    ):
        left, right = (
            (queue_tag, stage_tag) if direction == "in" else (stage_tag, queue_tag)
        )
        edge = f"'{left}' -> '{right}'"
        exception_text = str(exception).replace("\n", " ")
        self._log(
            "WARNING",
            f"Get from Edge({edge}): ({type(exception).__name__}){exception_text}.",
        )

    # ==== reporter ====
    def stop_reporter(self):
        self._log("DEBUG", "[Reporter] Stopped.")

    def loop_failed(self, exception):
        self._log(
            "ERROR",
            f"[Reporter] Loop error: {type(exception).__name__}({exception}).",
        )

    def pull_interval_failed(self, exception):
        self._log(
            "WARNING",
            f"[Reporter] Interval fetch failed: {type(exception).__name__}({exception}).",
        )

    def pull_tasks_failed(self, exception):
        self._log(
            "WARNING",
            f"[Reporter] Task injection fetch failed: {type(exception).__name__}({exception}).",
        )

    def inject_tasks_success(self, target_node, task_datas):
        self._log("INFO", f"[Reporter] Inject tasks {task_datas} into '{target_node}'.")

    def inject_tasks_failed(self, target_node, task_datas, exception):
        self._log(
            "WARNING",
            f"[Reporter] Inject tasks {task_datas} into '{target_node}' failed. "
            f"Error: {type(exception).__name__}({exception}).",
        )

    def push_errors_failed(self, exception):
        self._log(
            "WARNING",
            f"[Reporter] Error push failed: {type(exception).__name__}({exception}).",
        )

    def push_status_failed(self, exception):
        self._log(
            "WARNING",
            f"[Reporter] Status push failed: {type(exception).__name__}({exception}).",
        )

    def push_structure_failed(self, exception):
        self._log(
            "WARNING",
            f"[Reporter] Structure push failed: {type(exception).__name__}({exception}).",
        )

    def push_topology_failed(self, exception):
        self._log(
            "WARNING",
            f"[Reporter] Topology push failed: {type(exception).__name__}({exception}).",
        )
