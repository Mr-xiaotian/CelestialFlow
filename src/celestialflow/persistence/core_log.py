# persistence/core_log.py
from __future__ import annotations

from pathlib import Path
from time import localtime, strftime
from typing import Any, TextIO

from ..funnel import BaseInlet, BaseSpout
from ..observability.core_event import (
    NodeEndEvent,
    NodeStartEvent,
    TaskFailEvent,
    TaskInputEvent,
    TaskRetryEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
    TerminationInputEvent,
    TerminationMergeEvent,
    WorkerCrashEvent,
)
from ..observability.core_observer import Observer
from ..runtime.util_constant import LEVEL_DICT
from ..runtime.util_errors import InitializationError, InvalidOptionError


class LogSpout(BaseSpout):
    """
    日志监听线程，用于将日志写入文件
    """

    def __init__(self) -> None:
        """初始化日志监听器"""
        super().__init__()

        self.log_path: Path | None = None
        self._file: TextIO | None = None

    def _before_start(self) -> None:
        """创建 logs 目录并打开日志文件"""
        # 创建 logs 目录
        now = strftime("%Y-%m-%d", localtime())
        self.log_path = Path(f"logs/flow_log({now}).log")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # 打开日志文件
        # 使用行缓冲，让读取方能及时看到新增日志，
        # 同时避免重新引入显式的刷新计数机制。
        self._file = self.log_path.open("a", encoding="utf-8", buffering=1)

    def _handle_record(self, record: dict[str, Any]) -> None:
        """
        处理单条日志记录并写入日志文件。

        :param record: 包含 timestamp, level, message 的日志记录字典
        """
        timestamp: str = record["timestamp"]
        level: str = record["level"]
        message: str = record["message"]

        line = f"{timestamp} {level} {message}\n"

        if self._file is None:
            raise InitializationError("log file is not initialized")
        _ = self._file.write(line)

    def _after_stop(self) -> None:
        """关闭日志文件句柄。"""
        if self._file:
            self._file.close()
            self._file = None


class LogInlet(BaseInlet, Observer):
    """
    线程安全日志包装类，所有日志通过队列发送到监听线程写入。

    节点主链路事件（节点启停、任务输入/成功/失败/跳过）以观察者形式消费；
    图结构、终止信号、崩溃与上报器日志仍由执行路径直接调用对应方法。
    """

    def __init__(self, log_level: str = "INFO") -> None:
        """
        初始化日志收集器。

        :param log_level: 日志级别，低于此级别的日志不记录，默认 "INFO"
        """
        self.log_level: str = log_level.upper()

        if self.log_level not in LEVEL_DICT:
            raise InvalidOptionError(
                "log level", self.log_level, tuple(LEVEL_DICT.keys())
            )

    def _log(self, level: str, message: str) -> None:
        """
        记录一条日志，低于当前日志级别的消息将被忽略

        :param level: 日志级别
        :param message: 日志消息内容
        """
        timestamp = strftime("%Y-%m-%d %H:%M:%S", localtime())
        level_upper = level.upper()
        if level_upper not in LEVEL_DICT:
            return
        if LEVEL_DICT[level_upper] < LEVEL_DICT[self.log_level]:
            return
        super()._funnel(
            {"timestamp": timestamp, "level": level_upper, "message": message}
        )

    # ==== 任务图 ====

    def graph_start(
        self, graph_name: str, graph_mode: str, structure_list: list[str]
    ) -> None:
        """
        记录任务图启动及结构信息

        :param graph_name: 任务图名称
        :param graph_mode: 任务图运行模式
        :param structure_list: 任务图结构信息列表
        """
        self._log(
            "INFO", f"Graph '{graph_name}' start by {graph_mode}. Graph structure:"
        )
        for line in structure_list:
            self._log("INFO", line)

    def graph_end(self, graph_name: str, use_time: float) -> None:
        """
        记录任务图结束

        :param graph_name: 任务图名称
        :param use_time: 任务图运行耗时（秒）
        """
        self._log("INFO", f"Graph '{graph_name}' end. Use {use_time:.2f}s.")

    # ==== 节点 ====

    def on_node_start(self, event: NodeStartEvent) -> None:
        """
        记录节点启动

        :param event: 节点启动事件
        """
        text = (
            f"Node '{event.node}' start; "
            + f"execute {event.task_count} tasks by "
            + f"{event.execution_mode}-{event.max_workers}."
        )
        self._log("INFO", text)

    def on_node_end(self, event: NodeEndEvent) -> None:
        """
        记录节点结束及统计

        :param event: 节点结束事件
        """
        self._log(
            "INFO",
            f"Node '{event.node}' end; execute tasks by "
            + f"{event.execution_mode}-{event.max_workers}. Use {event.elapsed:.2f}s. "
            + f"{event.succeeded} tasks succeeded, {event.failed} tasks failed, "
            + f"{event.skipped} tasks skipped.",
        )

    def node_crash(self, node_name: str, exception: Exception) -> None:
        """
        记录节点崩溃。

        :param node_name: 节点名称
        :param exception: 异常对象
        """
        exception_type = type(exception).__name__
        exception_text = str(exception).replace("\n", " ")
        self._log(
            "CRITICAL",
            f"Node '{node_name}' crashed: ({exception_type}){exception_text}.",
        )

    # ==== 工作线程 ====

    def on_worker_crash(self, event: WorkerCrashEvent) -> None:
        """
        记录工作器崩溃

        :param event: 工作器崩溃事件
        """
        exception = event.exception
        exception_type = type(exception).__name__
        exception_text = str(exception).replace("\n", " ")
        self._log(
            "CRITICAL",
            f"In '{event.node}', Worker crashed: ({exception_type}){exception_text}.",
        )

    # ==== 任务 ====

    def on_task_input(self, event: TaskInputEvent) -> None:
        """
        记录任务输入

        :param event: 任务输入事件
        """
        self._log(
            "DEBUG",
            f"In '{event.node}', Task {event.task_repr} input. [{event.input_id}*]",
        )

    def on_task_success(self, event: TaskSuccessEvent) -> None:
        """
        记录任务成功

        :param event: 任务成功事件
        """
        self._log(
            "SUCCESS",
            f"In '{event.node}', Task {event.task_repr} succeeded. "
            + f"Result is {event.result_repr}. Used {event.elapsed:.2f}s. "
            + f"[{event.task_id}->{event.success_id}*]",
        )

    def on_task_fail(self, event: TaskFailEvent) -> None:
        """
        记录任务失败

        :param event: 任务失败事件
        """
        exception_type = type(event.exception).__name__
        exception_text = str(event.exception).replace("\n", " ")
        self._log(
            "ERROR",
            f"In '{event.node}', Task {event.task_repr} failed and can't retry: "
            + f"({exception_type}){exception_text}. "
            + f"[{event.task_id}->{event.error_id}*]",
        )

    def on_task_skip(self, event: TaskSkipEvent) -> None:
        """
        记录任务被跳过

        :param event: 任务跳过事件
        """
        self._log(
            "INFO",
            f"In '{event.node}', Task {event.task_repr} skipped. "
            + f"[{event.task_id}->{event.skip_id}*]",
        )

    def on_task_retry(self, event: TaskRetryEvent) -> None:
        """
        记录任务重试

        :param event: 任务重试事件
        """
        self._log(
            "WARNING",
            f"In '{event.node}', Task {event.task_repr} failed {event.retry_times} "
            + f"times and will retry: ({type(event.exception).__name__}). "
            + f"[{event.task_id}*]",
        )

    # ==== 终止信号 ====

    def on_termination_input(self, event: TerminationInputEvent) -> None:
        """
        记录终止信号输入

        :param event: 终止信号输入事件
        """
        self._log(
            "DEBUG",
            f"In '{event.node}', Termination input. [{event.termination_id}*]",
        )

    def on_termination_merge(self, event: TerminationMergeEvent) -> None:
        """
        记录终止信号合并

        :param event: 终止信号合并事件
        """
        self._log(
            "TRACE",
            f"In '{event.node}', Termination merge. "
            + f"[{event.parent_ids}->{event.termination_id}*]",
        )

    # ==== 上报器 ====

    def stop_reporter(self) -> None:
        """记录上报器停止"""
        self._log("DEBUG", "[Reporter] Stopped.")

    def loop_failed(self, exception: Exception) -> None:
        """
        记录上报器循环错误

        :param exception: 循环中发生的异常
        """
        self._log(
            "ERROR",
            f"[Reporter] Loop error: {type(exception).__name__}({exception}).",
        )

    def pull_interval_failed(self, exception: Exception) -> None:
        """
        记录拉取上报间隔失败

        :param exception: 拉取间隔时发生的异常
        """
        self._log(
            "WARNING",
            f"[Reporter] Pull 'interval' failed: {type(exception).__name__}({exception}).",
        )

    def pull_tasks_failed(self, exception: Exception) -> None:
        """
        记录拉取任务注入失败

        :param exception: 拉取任务时发生的异常
        """
        self._log(
            "WARNING",
            f"[Reporter] Pull 'task injection' failed: {type(exception).__name__}({exception}).",
        )

    def inject_tasks_success(self, target_node: str, task_datas: Any) -> None:
        """
        记录任务注入成功

        :param target_node: 注入目标节点名称
        :param task_datas: 注入的任务数据
        """
        self._log("INFO", f"[Reporter] Inject tasks {task_datas} into '{target_node}'.")

    def inject_tasks_failed(
        self,
        target_node: str,
        task_datas: Any,
        exception: Exception,
    ) -> None:
        """
        记录任务注入失败

        :param target_node: 注入目标节点名称
        :param task_datas: 注入的任务数据
        :param exception: 注入时发生的异常
        """
        self._log(
            "WARNING",
            f"[Reporter] Inject tasks {task_datas} into '{target_node}' failed. "
            + f"Error: {type(exception).__name__}({exception}).",
        )

    def push_errors_failed(self, exception: Exception) -> None:
        """
        记录推送错误信息失败

        :param exception: 推送时发生的异常
        """
        self._log(
            "WARNING",
            f"[Reporter] Push 'error' failed: {type(exception).__name__}({exception}).",
        )

    def push_status_failed(self, exception: Exception) -> None:
        """
        记录推送状态信息失败

        :param exception: 推送时发生的异常
        """
        self._log(
            "WARNING",
            f"[Reporter] Push 'status' failed: {type(exception).__name__}({exception}).",
        )

    def push_graph_meta_failed(self, exception: Exception) -> None:
        """
        记录推送图元信息失败

        :param exception: 推送时发生的异常
        """
        self._log(
            "WARNING",
            f"[Reporter] Push 'graph_meta' failed: {type(exception).__name__}({exception}).",
        )

    def shutdown_failed(self, exception: Exception) -> None:
        """
        记录通知服务端会话结束失败

        :param exception: 通知时发生的异常
        """
        self._log(
            "WARNING",
            f"[Reporter] Notify 'shutdown' failed: {type(exception).__name__}({exception}).",
        )
