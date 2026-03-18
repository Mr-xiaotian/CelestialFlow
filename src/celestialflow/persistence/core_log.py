# persistence/core_log.py
from pathlib import Path
from time import localtime, strftime

from ..runtime.util_errors import LogLevelError
from .core_base import BaseListener, BaseSinker
from .util_constant import LEVEL_DICT


class LogListener(BaseListener):
    """
    日志监听线程，用于将日志写入文件
    """

    def __init__(self):
        super().__init__()

        self.log_queue = self.queue
        self.log_path: Path | None = None
        self._file = None

    def _before_start(self) -> None:
        # 创建 logs 目录
        now = strftime("%Y-%m-%d", localtime())
        self.log_path = Path(f"logs/task_logger({now}).log")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # 打开日志文件
        self._file = self.log_path.open("a", encoding="utf-8")

    def _handle_record(self, record: dict) -> None:
        timestamp = record["timestamp"]
        level = record["level"]
        message = record["message"]

        line = f"{timestamp} {level} {message}\n"

        self._file.write(line)
        self._file.flush()

    def _after_stop(self) -> None:
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None


class LogSinker(BaseSinker):
    """
    多进程安全日志包装类，所有日志通过队列发送到监听进程写入
    """

    def __init__(self, log_queue, log_level: str = "SUCCESS") -> None:
        super().__init__(log_queue)
        self.log_queue = self.queue
        self.log_level: str = log_level.upper()

        if self.log_level not in LEVEL_DICT:
            raise LogLevelError(self.log_level)

    def _sink(self, level: str, message: str) -> None:
        timestamp = strftime("%Y-%m-%d %H:%M:%S", localtime())
        level_upper = level.upper()
        if level_upper not in LEVEL_DICT:
            return
        if LEVEL_DICT[level_upper] < LEVEL_DICT[self.log_level]:
            return
        super()._sink(
            {"timestamp": timestamp, "level": level_upper, "message": message}
        )

    # ==== graph ====
    def start_graph(self, structure_list: list[str]) -> None:
        self._sink("INFO", f"Starting TaskGraph. Graph structure:")
        for line in structure_list:
            self._sink("INFO", line)

    def end_graph(self, use_time: float) -> None:
        self._sink("INFO", f"TaskGraph end. Use {use_time:.2f} second.")

    # ==== layer ====
    def start_layer(self, layer: list[str], layer_level: int) -> None:
        self._sink("INFO", f"Layer {layer} start. Layer level: {layer_level}.")

    def end_layer(self, layer: list[str], use_time: float) -> None:
        self._sink("INFO", f"Layer {layer} end. Use {use_time:.2f} second.")

    # ==== stage ====
    def start_stage(self, stage_tag: str, stage_mode: str, execution_mode: str, worker_limit: int) -> None:
        worker_repr = f"({worker_limit} workers)" if execution_mode != "serial" else ""
        text = f"'{stage_tag}' start in {stage_mode}; execute tasks by {execution_mode}{worker_repr}."
        self._sink("INFO", text)

    def end_stage(
        self,
        stage_tag: str,
        stage_mode: str,
        execution_mode: str,
        use_time: float,
        success_num: int,
        failed_num: int,
        duplicated_num: int,
    ) -> None:
        self._sink(
            "INFO",
            f"'{stage_tag}' end in {stage_mode}; execute tasks by {execution_mode}. Use {use_time:.2f} second. "
            f"{success_num} tasks successed, {failed_num} tasks failed, {duplicated_num} tasks duplicated.",
        )

    # ==== executor ====
    def start_executor(self, func_name: str, task_num: int, execution_mode_desc: str) -> None:
        text = (
            f"'Executor[{func_name}]' start; execute {task_num} tasks by {execution_mode_desc}."
        )
        self._sink("INFO", text)

    def end_executor(
        self,
        func_name: str,
        execution_mode: str,
        use_time: float,
        success_num: int,
        failed_num: int,
        duplicated_num: int,
    ) -> None:
        self._sink(
            "INFO",
            f"'Executor[{func_name}]' end; execute tasks by {execution_mode}. Use {use_time:.2f} second. "
            f"{success_num} tasks successed, {failed_num} tasks failed, {duplicated_num} tasks duplicated.",
        )

    # ==== process ====
    def process_termination_attempt(self, process_name: str) -> None:
        self._sink(
            "WARNING",
            f"Process '{process_name}' is still running; attempting graceful termination.",
        )

    def process_termination_timeout(self, process_name: str) -> None:
        self._sink(
            "WARNING",
            f"Process '{process_name}' did not exit within the termination timeout.",
        )

    def process_exit(self, process_name: str, exitcode: int | None) -> None:
        self._sink(
            "DEBUG", f"Process '{process_name}' exited with exit code {exitcode}."
        )

    # ==== task ====
    def task_input(self, func_name: str, task_info: str, source: str, input_id: int) -> None:
        self._sink(
            "DEBUG",
            f"In '{func_name}', Task {task_info} input into {source}. [{input_id}*]",
        )

    def task_success(
        self,
        func_name: str,
        task_info: str,
        execution_mode: str,
        result_info: str,
        use_time: float,
        parent_id: int,
        success_id: int,
    ) -> None:
        self._sink(
            "SUCCESS",
            f"In '{func_name}', Task {task_info} completed by {execution_mode}. Result is {result_info}. Used {use_time:.2f} seconds. [{parent_id}->{success_id}*]",
        )

    def task_retry(
        self, func_name: str, task_info: str, retry_times: int, exception: Exception, parent_id: int, retry_id: int
    ) -> None:
        self._sink(
            "WARNING",
            f"In '{func_name}', Task {task_info} failed {retry_times} times and will retry: ({type(exception).__name__}). [{parent_id}->{retry_id}*]",
        )

    def task_error(self, func_name: str, task_info: str, exception: Exception, parent_id: int, error_id: int) -> None:
        exception_text = str(exception).replace("\n", " ")
        self._sink(
            "ERROR",
            f"In '{func_name}', Task {task_info} failed and can't retry: ({type(exception).__name__}){exception_text}. [{parent_id}->{error_id}*]",
        )

    def task_duplicate(self, func_name: str, task_info: str, parent_id: int, duplicate_id: int) -> None:
        self._sink(
            "WARNING",
            f"In '{func_name}', Task {task_info} has been duplicated. [{parent_id}->{duplicate_id}*]",
        )

    # ==== splitter ====
    def split_trace(self, func_name: str, part_index: int, part_total: int, parent_id: int, split_id: int) -> None:
        self._sink(
            "TRACE",
            f"In '{func_name}', Task split part {part_index}/{part_total}. [{parent_id}->{split_id}*]",
        )

    def split_success(self, func_name: str, task_info: str, split_count: int, use_time: float) -> None:
        self._sink(
            "SUCCESS",
            f"In '{func_name}', Task {task_info} has split into {split_count} parts. Used {use_time:.2f} seconds.",
        )

    # ==== router ====
    def route_success(
        self, func_name: str, task_info: str, target_node: str, use_time: float, parent_id: int, route_id: int
    ) -> None:
        self._sink(
            "SUCCESS",
            f"In '{func_name}', Task {task_info} has routed to {target_node}. Used {use_time:.2f} seconds. [{parent_id}->{route_id}*]",
        )

    # ==== termination ====
    def termination_input(self, func_name: str, source: str, termination_id: int) -> None:
        self._sink(
            "DEBUG",
            f"In '{func_name}', Termination input into {source}. [{termination_id}*]",
        )

    def termination_merge(self, func_name: str, parent_ids: list[int], termination_id: int) -> None:
        self._sink(
            "TRACE",
            f"In '{func_name}', Termination merge. [{parent_ids}->{termination_id}*]",
        )

    # ==== queue ====
    def put_item(self, item_type: str, item_id: int, left_tag: str, right_tag: str) -> None:
        edge = f"'{left_tag}' -> '{right_tag}'"
        self._sink("TRACE", f"Put {item_type}#{item_id} into Edge({edge}).")

    def put_item_error(self, left_tag: str, right_tag: str, exception: Exception) -> None:
        edge = f"'{left_tag}' -> '{right_tag}'"
        exception_text = str(exception).replace("\n", " ")
        self._sink(
            "WARNING",
            f"Put into Edge({edge}): ({type(exception).__name__}){exception_text}.",
        )

    def get_item(self, item_type: str, item_id: int, left_tag: str, right_tag: str) -> None:
        edge = f"'{left_tag}' -> '{right_tag}'"
        self._sink("TRACE", f"Get {item_type}#{item_id} from Edge({edge}).")

    def get_item_error(
        self, left_tag: str, right_tag: str, exception: Exception
    ) -> None:
        edge = f"'{left_tag}' -> '{right_tag}'"
        exception_text = str(exception).replace("\n", " ")
        self._sink(
            "WARNING",
            f"Get from Edge({edge}): ({type(exception).__name__}){exception_text}.",
        )

    # ==== reporter ====
    def stop_reporter(self) -> None:
        self._sink("DEBUG", "[Reporter] Stopped.")

    def loop_failed(self, exception: Exception) -> None:
        self._sink(
            "ERROR",
            f"[Reporter] Loop error: {type(exception).__name__}({exception}).",
        )

    def pull_interval_failed(self, exception: Exception) -> None:
        self._sink(
            "WARNING",
            f"[Reporter] Pull 'interval' failed: {type(exception).__name__}({exception}).",
        )

    def pull_tasks_failed(self, exception: Exception) -> None:
        self._sink(
            "WARNING",
            f"[Reporter] Pull 'task injection' failed: {type(exception).__name__}({exception}).",
        )

    def inject_tasks_success(self, target_node: str, task_datas) -> None:
        self._sink(
            "INFO", f"[Reporter] Inject tasks {task_datas} into '{target_node}'."
        )

    def inject_tasks_failed(self, target_node: str, task_datas, exception: Exception) -> None:
        self._sink(
            "WARNING",
            f"[Reporter] Inject tasks {task_datas} into '{target_node}' failed. "
            f"Error: {type(exception).__name__}({exception}).",
        )

    def push_errors_failed(self, exception: Exception) -> None:
        self._sink(
            "WARNING",
            f"[Reporter] Push 'error' failed: {type(exception).__name__}({exception}).",
        )

    def push_status_failed(self, exception: Exception) -> None:
        self._sink(
            "WARNING",
            f"[Reporter] Push 'status' failed: {type(exception).__name__}({exception}).",
        )

    def push_structure_failed(self, exception: Exception) -> None:
        self._sink(
            "WARNING",
            f"[Reporter] Push 'structure' failed: {type(exception).__name__}({exception}).",
        )

    def push_topology_failed(self, exception: Exception) -> None:
        self._sink(
            "WARNING",
            f"[Reporter] Push 'topology' failed: {type(exception).__name__}({exception}).",
        )

    def push_summary_failed(self, exception: Exception) -> None:
        self._sink(
            "WARNING",
            f"[Reporter] Push 'summary' failed: {type(exception).__name__}({exception}).",
        )
