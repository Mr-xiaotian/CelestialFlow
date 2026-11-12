# persist/core_log.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import localtime, strftime
from typing import TextIO

from ..funnel import BaseInlet, BaseSpout
from ..observer import (
    Event,
    GraphEndEvent,
    GraphStartEvent,
    NodeEndEvent,
    NodeStartEvent,
    Observer,
    TaskFailEvent,
    TaskInputEvent,
    TaskRetryEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
    TerminationInputEvent,
    TerminationMergeEvent,
)
from ..runtime.util_constant import LEVEL_DICT
from ..runtime.util_errors import InitializationError, InvalidOptionError
from ..runtime.util_log_level import DEFAULT_LOG_LEVEL
from ..runtime.util_types import MetricsView
from .util_render import render_structure_list


@dataclass(frozen=True, slots=True)
class LogRecord:
    """单条日志记录。

    :param timestamp: 格式化后的时间戳
    :param level: 日志级别
    :param message: 日志消息
    """

    timestamp: str
    level: str
    message: str


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

    def _handle_record(self, record: LogRecord) -> None:
        """
        处理单条日志记录并写入日志文件。

        :param record: 日志记录
        """
        line = f"{record.timestamp} {record.level} {record.message}\n"

        if self._file is None:
            raise InitializationError("log file is not initialized")
        _ = self._file.write(line)

    def _after_stop(self) -> None:
        """关闭日志文件句柄。"""
        if self._file:
            self._file.close()
            self._file = None


class LogInlet(BaseInlet):
    """Log 记录入口。

    将日志记录投递到绑定的 spout。
    """

    def send(self, record: LogRecord) -> None:
        """
        将一条日志记录送入 spout 队列。

        :param record: 日志记录
        """
        super().send(record)


class LogObserver(Observer):
    """运行日志观察者（门面）。

    将观测事件翻译为日志记录，经 :class:`LogInlet` 投递到后台
    :class:`LogSpout` 写入文件；同时管理 spout 的启停并暴露日志文件路径。

    图结构、节点启停、任务输入/成功/失败/跳过/重试、终止信号均在
    :meth:`on_event` 中按事件类型记录。
    """

    def __init__(
        self,
        metrics_view: MetricsView,
        log_level: str = DEFAULT_LOG_LEVEL,
    ) -> None:
        """
        初始化日志观察者并绑定 spout 与 inlet。

        :param metrics_view: 指标只读视图，用于记录节点汇总
        :param log_level: 日志级别，低于此级别的日志不记录，默认
            ``DEFAULT_LOG_LEVEL``
        :raises InvalidOptionError: ``log_level`` 不在允许的级别集合中
        """
        self._metrics_view = metrics_view
        self.log_level: str = log_level.upper()

        if self.log_level not in LEVEL_DICT:
            raise InvalidOptionError(
                "log level", self.log_level, tuple(LEVEL_DICT.keys())
            )

        self._spout = LogSpout()
        self._inlet = LogInlet().bind_spout(self._spout)

    @property
    def log_path(self) -> Path | None:
        """日志文件路径；spout 尚未启动时为 ``None``。"""
        return self._spout.log_path

    def start(self) -> None:
        """启动后台写入循环并打开日志文件。"""
        self._spout.start()

    def stop(self) -> None:
        """停止后台写入循环并关闭日志文件。"""
        self._spout.stop()

    def _log(self, level: str, message: str) -> None:
        """
        记录一条日志，低于当前日志级别的消息将被忽略

        :param level: 日志级别
        :param message: 日志消息内容
        """
        level_upper = level.upper()
        if level_upper not in LEVEL_DICT:
            return
        if LEVEL_DICT[level_upper] < LEVEL_DICT[self.log_level]:
            return

        timestamp = strftime("%Y-%m-%d %H:%M:%S", localtime())
        self._inlet.send(
            LogRecord(timestamp=timestamp, level=level_upper, message=message)
        )

    def on_event(self, event: Event) -> None:
        """
        接收并处理观测事件，按事件类型记录日志。

        - 图级：记录启动结构信息与结束耗时；
        - 节点级：记录节点启停与执行统计；
        - 任务级：记录输入、成功、失败、跳过与重试；
        - 终止信号：记录输入与合并。

        :param event: 任意观测事件
        """
        match event:
            case GraphStartEvent():
                structure_list = render_structure_list(
                    event.nodes, event.edges, event.source_nodes
                )
                self._log(
                    "INFO",
                    f"Graph '{event.graph}' start by {event.graph_mode}. Graph structure:",
                )
                for line in structure_list:
                    self._log("INFO", line)
            case GraphEndEvent():
                self._log(
                    "INFO", f"Graph '{event.graph}' end. Use {event.elapsed:.2f}s."
                )
            case NodeStartEvent():
                node_metrics = self._metrics_view.get_node_metrics(event.node)
                node_inputs = node_metrics.input_total if node_metrics is not None else 0
                text = (
                    f"Node '{event.node}' start; "
                    + f"execute {node_inputs} tasks by "
                    + f"{event.execution_mode}-{event.max_workers}."
                )
                self._log("INFO", text)
            case NodeEndEvent():
                node_metrics = self._metrics_view.get_node_metrics(event.node)
                node_success = node_metrics.succeeded if node_metrics is not None else 0
                node_fail = node_metrics.failed if node_metrics is not None else 0
                node_skip = node_metrics.skipped if node_metrics is not None else 0
                self._log(
                    "INFO",
                    f"Node '{event.node}' end; execute tasks by "
                    + f"{event.execution_mode}-{event.max_workers}. "
                    + f"Use {event.elapsed:.2f}s. "
                    + f"{node_success} tasks succeeded, {node_fail} tasks failed, "
                    + f"{node_skip} tasks skipped.",
                )
            case TaskInputEvent():
                origin = event.from_node if event.from_node is not None else "external"
                self._log(
                    "DEBUG",
                    f"In '{event.node}', Task {event.task_repr} input from {origin}. "
                    + f"[{event.input_id}*]",
                )
            case TaskSuccessEvent():
                self._log(
                    "SUCCESS",
                    f"In '{event.node}', Task {event.task_repr} succeeded. "
                    + f"Result is {event.result_repr}. Used {event.elapsed:.2f}s. "
                    + f"[{event.task_id}->{event.success_id}*]",
                )
            case TaskFailEvent():
                exception_type = type(event.exception).__name__
                exception_text = str(event.exception).replace("\n", " ")
                self._log(
                    "ERROR",
                    f"In '{event.node}', Task {event.task_repr} failed and can't retry: "
                    + f"({exception_type}){exception_text}. "
                    + f"[{event.task_id}->{event.error_id}*]",
                )
            case TaskSkipEvent():
                self._log(
                    "SUCCESS",
                    f"In '{event.node}', Task {event.task_repr} skipped. "
                    + f"[{event.task_id}->{event.skip_id}*]",
                )
            case TaskRetryEvent():
                self._log(
                    "WARNING",
                    f"In '{event.node}', Task {event.task_repr} failed "
                    + f"{event.retry_times} times and will retry: "
                    + f"({type(event.exception).__name__}). "
                    + f"[{event.task_id}*]",
                )
            case TerminationInputEvent():
                self._log(
                    "DEBUG",
                    f"In '{event.node}', Termination input. [{event.termination_id}*]",
                )
            case TerminationMergeEvent():
                self._log(
                    "TRACE",
                    f"In '{event.node}', Termination merge. "
                    + f"[{event.parent_ids}->{event.termination_id}*]",
                )
            case _:
                pass
