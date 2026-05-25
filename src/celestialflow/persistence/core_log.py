# persistence/core_log.py
from __future__ import annotations

from pathlib import Path
from queue import Queue
from time import localtime, strftime
from typing import Any, TextIO

from ..funnel import BaseInlet, BaseSpout
from ..runtime.util_errors import InitializationError, LogLevelError
from .util_constant import LEVEL_DICT


class LogSpout(BaseSpout):
    """
    日志监听线程，用于将日志写入文件
    """

    def __init__(self) -> None:
        """初始化日志监听器"""
        super().__init__()

        self.log_path: Path | None = None
        self._file: TextIO | None = None

        # 批量刷新：日志量远大于错误量，阈值设更高
        self._flush_every: int = 5
        self._flush_counter: int = 0

    def _before_start(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """创建 logs 目录并打开日志文件"""
        # 创建 logs 目录
        now = strftime("%Y-%m-%d", localtime())
        self.log_path = Path(f"logs/task_logger({now}).log")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # 打开日志文件
        self._file = self.log_path.open("a", encoding="utf-8")

        # 初始化计数器
        self._flush_counter = 0

    def _handle_record(self, record: dict[str, Any]) -> None:  # pyright: ignore[reportImplicitOverride]
        """
        处理单条日志记录，批量写入日志文件。
        每 _flush_every 条记录才 flush 一次。

        :param record: 包含 timestamp, level, message 的日志记录字典
        """
        timestamp: Any = record["timestamp"]
        level: Any = record["level"]
        message: Any = record["message"]

        line = f"{timestamp} {level} {message}\n"

        if self._file is None:
            raise InitializationError("log file is not initialized")
        _ = self._file.write(line)
        self._flush_counter += 1

        if self._flush_counter >= self._flush_every:
            self._file.flush()
            self._flush_counter = 0

    def _after_stop(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """关闭日志文件句柄，确保剩余缓冲落盘"""
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None


class LogInlet(BaseInlet):
    """
    线程安全日志包装类，所有日志通过队列发送到监听线程写入
    """

    def __init__(self, log_queue: Queue[Any], log_level: str = "INFO") -> None:
        """
        初始化日志收集器

        :param log_queue: 日志队列
        :param log_level: 日志级别，低于此级别的日志不记录，默认 "INFO"
        """
        super().__init__(log_queue)
        self.log_level: str = log_level.upper()

        if self.log_level not in LEVEL_DICT:
            raise LogLevelError(self.log_level)

    def _log(self, level: str, message: str | None = None) -> None:
        """
        记录一条日志，低于当前日志级别的消息将被忽略

        :param level: 日志级别
        :param message: 日志消息内容，默认 None（跳过）
        """
        if message is None:
            return
        timestamp = strftime("%Y-%m-%d %H:%M:%S", localtime())
        level_upper = level.upper()
        if level_upper not in LEVEL_DICT:
            return
        if LEVEL_DICT[level_upper] < LEVEL_DICT[self.log_level]:
            return
        super()._funnel(
            {"timestamp": timestamp, "level": level_upper, "message": message}
        )

    # ==== graph ====
    def start_graph(self, structure_list: list[str]) -> None:
        """记录任务图启动及结构信息"""
        self._log("INFO", "Starting TaskGraph. Graph structure:")
        for line in structure_list:
            self._log("INFO", line)

    def end_graph(self, use_time: float) -> None:
        """记录任务图结束"""
        self._log("INFO", f"TaskGraph end. Use {use_time:.2f} second.")

    # ==== layer ====
    def start_layer(self, layer: list[str], layer_level: int) -> None:
        """记录分层调度中某一层的启动"""
        self._log("INFO", f"Layer {layer} start. Layer level: {layer_level}.")

    def end_layer(self, layer: list[str], use_time: float) -> None:
        """记录分层调度中某一层的结束"""
        self._log("INFO", f"Layer {layer} end. Use {use_time:.2f} second.")

    # ==== stage ====
    def start_stage(
        self,
        stage_name: str,
        stage_mode: str,
        execution_mode_desc: str,
    ) -> None:
        """记录节点启动"""
        text = f"'{stage_name}' start in {stage_mode}; execute tasks by {execution_mode_desc}."
        self._log("INFO", text)

    def end_stage(
        self,
        stage_name: str,
        stage_mode: str,
        execution_mode_desc: str,
        use_time: float,
        success_num: int,
        failed_num: int,
        duplicated_num: int,
    ) -> None:
        """记录节点结束及统计"""
        self._log(
            "INFO",
            f"'{stage_name}' end in {stage_mode}; execute tasks by {execution_mode_desc}. Use {use_time:.2f} second. "
            + f"{success_num} tasks succeeded, {failed_num} tasks failed, {duplicated_num} tasks duplicated.",
        )

    # ==== executor ====
    def start_executor(
        self, name: str, func_name: str, task_num: int, execution_mode_desc: str
    ) -> None:
        """记录执行器启动"""
        text = f"'{name}[{func_name}]' start; execute {task_num} tasks by {execution_mode_desc}."
        self._log("INFO", text)

    def end_executor(
        self,
        name: str,
        func_name: str,
        execution_mode_desc: str,
        use_time: float,
        success_num: int,
        failed_num: int,
        duplicated_num: int,
    ) -> None:
        """记录执行器结束及统计"""
        self._log(
            "INFO",
            f"'{name}[{func_name}]' end; execute tasks by {execution_mode_desc}. Use {use_time:.2f} second. "
            + f"{success_num} tasks succeeded, {failed_num} tasks failed, {duplicated_num} tasks duplicated.",
        )

    # ==== task ====
    def task_input(
        self, func_name: str, task_repr: str, source: str, input_id: int
    ) -> None:
        """记录任务输入"""
        self._log(
            "DEBUG",
            f"In '{func_name}', Task {task_repr} input into {source}. [{input_id}*]",
        )

    def task_success(
        self,
        func_name: str,
        task_repr: str,
        execution_mode: str,
        result_repr: str,
        use_time: float,
        parent_id: int,
        success_id: int,
    ) -> None:
        """记录任务成功"""
        self._log(
            "SUCCESS",
            f"In '{func_name}', Task {task_repr} succeeded by {execution_mode}. Result is {result_repr}. Used {use_time:.2f}s. [{parent_id}->{success_id}*]",
        )

    def task_retry(
        self,
        func_name: str,
        task_repr: str,
        retry_times: int,
        exception: Exception,
        parent_id: int,
        retry_id: int,
    ) -> None:
        """记录任务重试"""
        self._log(
            "WARNING",
            f"In '{func_name}', Task {task_repr} failed {retry_times} times and will retry: ({type(exception).__name__}). [{parent_id}->{retry_id}*]",
        )

    def task_error(
        self,
        func_name: str,
        task_repr: str,
        exception: Exception,
        parent_id: int,
        error_id: int,
    ) -> None:
        """记录任务失败"""
        exception_text = str(exception).replace("\n", " ")
        self._log(
            "ERROR",
            f"In '{func_name}', Task {task_repr} failed and can't retry: ({type(exception).__name__}){exception_text}. [{parent_id}->{error_id}*]",
        )

    def task_duplicate(
        self, func_name: str, task_repr: str, parent_id: int, duplicate_id: int
    ) -> None:
        """记录重复任务"""
        self._log(
            "WARNING",
            f"In '{func_name}', Task {task_repr} has been duplicated. [{parent_id}->{duplicate_id}*]",
        )

    # ==== splitter ====
    def split_trace(
        self,
        func_name: str,
        part_index: int,
        part_total: int,
        parent_id: int,
        split_id: int,
    ) -> None:
        """记录 split 子任务分发"""
        self._log(
            "TRACE",
            f"In '{func_name}', Task split part {part_index}/{part_total}. [{parent_id}->{split_id}*]",
        )

    def split_success(
        self, func_name: str, task_repr: str, split_count: int, use_time: float
    ) -> None:
        """记录 split 成功"""
        self._log(
            "SUCCESS",
            f"In '{func_name}', Task {task_repr} has split into {split_count} parts. Used {use_time:.2f}s.",
        )

    # ==== router ====
    def route_success(
        self,
        func_name: str,
        task_repr: str,
        target_node: str,
        use_time: float,
        parent_id: int,
        route_id: int,
    ) -> None:
        """记录路由成功"""
        self._log(
            "SUCCESS",
            f"In '{func_name}', Task {task_repr} has routed to {target_node}. Used {use_time:.2f}s. [{parent_id}->{route_id}*]",
        )

    # ==== termination ====
    def termination_input(
        self, func_name: str, source: str, termination_id: int
    ) -> None:
        """记录终止信号输入"""
        self._log(
            "DEBUG",
            f"In '{func_name}', Termination input into {source}. [{termination_id}*]",
        )

    def termination_merge(
        self, func_name: str, parent_ids: list[int], termination_id: int
    ) -> None:
        """记录终止信号合并"""
        self._log(
            "TRACE",
            f"In '{func_name}', Termination merge. [{parent_ids}->{termination_id}*]",
        )

    # ==== queue ====
    def put_item(
        self, item_type: str, item_id: int, in_name: str, out_name: str
    ) -> None:
        """记录队列 put 操作"""
        edge = f"'{in_name}' -> '{out_name}'"
        self._log("TRACE", f"Put {item_type}#{item_id} into Edge({edge}).")

    def put_item_error(self, in_name: str, out_name: str, exception: Exception) -> None:
        """记录队列 put 失败"""
        edge = f"'{in_name}' -> '{out_name}'"
        exception_text = str(exception).replace("\n", " ")
        self._log(
            "WARNING",
            f"Put into Edge({edge}): ({type(exception).__name__}){exception_text}.",
        )

    def get_item(
        self, item_type: str, item_id: int, in_name: str, out_name: str
    ) -> None:
        """记录队列 get 操作"""
        edge = f"'{in_name}' -> '{out_name}'"
        self._log("TRACE", f"Get {item_type}#{item_id} from Edge({edge}).")

    def get_item_error(self, in_name: str, out_name: str, exception: Exception) -> None:
        """记录队列 get 失败"""
        edge = f"'{in_name}' -> '{out_name}'"
        exception_text = str(exception).replace("\n", " ")
        self._log(
            "WARNING",
            f"Get from Edge({edge}): ({type(exception).__name__}){exception_text}.",
        )

    # ==== reporter ====
    def stop_reporter(self) -> None:
        """记录上报器停止"""
        self._log("DEBUG", "[Reporter] Stopped.")

    def loop_failed(self, exception: Exception) -> None:
        """记录上报器循环错误"""
        self._log(
            "ERROR",
            f"[Reporter] Loop error: {type(exception).__name__}({exception}).",
        )

    def pull_interval_failed(self, exception: Exception) -> None:
        """记录拉取上报间隔失败"""
        self._log(
            "WARNING",
            f"[Reporter] Pull 'interval' failed: {type(exception).__name__}({exception}).",
        )

    def pull_history_limit_failed(self, exception: Exception) -> None:
        """记录拉取历史限制失败"""
        self._log(
            "WARNING",
            f"[Reporter] Pull 'history limit' failed: {type(exception).__name__}({exception}).",
        )

    def pull_tasks_failed(self, exception: Exception) -> None:
        """记录拉取任务注入失败"""
        self._log(
            "WARNING",
            f"[Reporter] Pull 'task injection' failed: {type(exception).__name__}({exception}).",
        )

    def inject_tasks_success(self, target_node: str, task_datas: Any) -> None:
        """记录任务注入成功"""
        self._log("INFO", f"[Reporter] Inject tasks {task_datas} into '{target_node}'.")

    def inject_tasks_failed(
        self,
        target_node: str,
        task_datas: Any,
        exception: Exception,
    ) -> None:
        """记录任务注入失败"""
        self._log(
            "WARNING",
            f"[Reporter] Inject tasks {task_datas} into '{target_node}' failed. "
            + f"Error: {type(exception).__name__}({exception}).",
        )

    def push_errors_failed(self, exception: Exception) -> None:
        """记录推送错误信息失败"""
        self._log(
            "WARNING",
            f"[Reporter] Push 'error' failed: {type(exception).__name__}({exception}).",
        )

    def push_status_failed(self, exception: Exception) -> None:
        """记录推送状态信息失败"""
        self._log(
            "WARNING",
            f"[Reporter] Push 'status' failed: {type(exception).__name__}({exception}).",
        )

    def push_structure_failed(self, exception: Exception) -> None:
        """记录推送结构信息失败"""
        self._log(
            "WARNING",
            f"[Reporter] Push 'structure' failed: {type(exception).__name__}({exception}).",
        )

    def push_analysis_failed(self, exception: Exception) -> None:
        """记录推送分析信息失败"""
        self._log(
            "WARNING",
            f"[Reporter] Push 'analysis' failed: {type(exception).__name__}({exception}).",
        )

    def push_summary_failed(self, exception: Exception) -> None:
        """记录推送摘要信息失败"""
        self._log(
            "WARNING",
            f"[Reporter] Push 'summary' failed: {type(exception).__name__}({exception}).",
        )

    def push_history_failed(self, exception: Exception) -> None:
        """记录推送历史信息失败"""
        self._log(
            "WARNING",
            f"[Reporter] Push 'history' failed: {type(exception).__name__}({exception}).",
        )
