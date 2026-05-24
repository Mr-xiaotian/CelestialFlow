# runtime/core_queue.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .core_envelope import TaskEnvelope
from .util_errors import (
    ConfigurationError,
    DuplicateNodeError,
    TerminationMergeError,
    UnknownNodeError,
)
from .util_types import TerminationIdPool, TerminationSignal

if TYPE_CHECKING:
    from ..persistence import LogInlet


# ==== TaskInQueue ====
class TaskInQueue:
    """任务输入队列，聚合多个上游来源的任务和终止信号。"""

    queue: Any
    source_names: list[str]
    out_name: str
    log_inlet: "LogInlet"
    termination_dict: dict[str, int]

    # ==== 初始化 ====
    def __init__(
        self,
        queue: Any,
        source_names: list[str],
        out_name: str,
        log_inlet: "LogInlet",
    ) -> None:
        """
        初始化任务入队

        :param queue: 队列对象
        :param source_names: 上游节点名称列表
        :param out_name: 当前节点唯一名称
        :param log_inlet: 日志记录器
        """
        self.queue = queue
        self.source_names = source_names
        self.out_name = out_name
        self.log_inlet = log_inlet

        self.termination_dict = {}

    # ==== 日志 ====
    def _log_put(self, item: TaskEnvelope | TerminationSignal) -> None:
        """
        记录任务入队日志

        :param item: 入队的任务或终止信号
        """
        if isinstance(item, TaskEnvelope):
            t = "task"
        else:
            t = "termination"
        self.log_inlet.put_item(t, item.id, item.source, self.out_name)

    def _log_get(self, item: TaskEnvelope | TerminationSignal) -> None:
        """
        记录任务出队日志

        :param item: 出队的任务或终止信号
        """
        if isinstance(item, TaskEnvelope):
            t = "task"
        else:
            t = "termination"
        self.log_inlet.get_item(t, item.id, item.source, self.out_name)

    def add_source_name(self, name: str) -> None:
        """
        添加入队来源名称

        :param name: 入队来源名称
        :raises ValueError: 如果名称已存在
        """
        if name in self.source_names:
            raise DuplicateNodeError(f"duplicate queue source name: {name}")
        self.source_names.append(name)

    # ==== 终止 ====
    def _record_termination(self, signal: TerminationSignal) -> None:
        """
        记录入队来源的终止信号

        :param signal: 入队来源的终止信号
        """
        source = signal.source

        valid_sources = set(self.source_names) | {"input"}
        if source not in valid_sources:
            raise UnknownNodeError(f"unknown queue source name: {source}")

        self.termination_dict[source] = signal.id

    def _can_merge_termination(self) -> bool:
        """
        判断是否可以合并普通输入队列的终止信号
        """
        return all(name in self.termination_dict for name in self.source_names)

    def _merge_termination(self) -> TerminationIdPool:
        """
        合并所有输入队列的终止信号

        这里只合并来自 source_names 的 termination，不处理：
        - input 注入的直接终止
        - self.out_name 的 merge 后终止

        :return: 合并后的终止信号池
        """
        missing_names = [
            name for name in self.source_names if name not in self.termination_dict
        ]
        if missing_names:
            raise TerminationMergeError(
                f"cannot merge termination, missing source names: {missing_names}"
            )

        return TerminationIdPool(
            ids=[self.termination_dict[name] for name in self.source_names]
        )

    # ==== put / get ====
    def put(self, item: TaskEnvelope | TerminationSignal) -> None:
        """
        入队任务或终止信号

        :param item: 要入队的任务或终止信号
        """
        try:
            self.queue.put(item)
            self._log_put(item)
        except Exception as e:
            self.log_inlet.put_item_error(item.source, self.out_name, e)

    def get(self) -> TaskEnvelope | TerminationIdPool:
        """
        出队任务或终止符号id池

        :return: 出队的任务或终止符号id池
        """
        while True:
            item: TaskEnvelope | TerminationSignal = self.queue.get()
            result = self._deal_get_item(item)
            if result is None:
                continue
            return result

    def _deal_get_item(
        self, item: TaskEnvelope | TerminationSignal
    ) -> TaskEnvelope | TerminationIdPool | None:
        """
        处理出队的任务或终止符号

        :param item: 出队的任务或终止信号
        :return: 处理后的任务或终止符号id池
        """
        self._log_get(item)

        if isinstance(item, TaskEnvelope):
            return item

        self._record_termination(item)
        if "input" in self.termination_dict:
            # 外部终止符注入, 直接退出
            return TerminationIdPool(ids=[self.termination_dict["input"]])

        elif self._can_merge_termination():
            # 所有上游终止，合并终止信号
            return self._merge_termination()

        # 信号已记录但尚未集齐所有上游，继续等待
        return None

    def drain(self) -> list[TaskEnvelope]:
        """
        清空队列中的所有任务，返回所有任务列表
        并记录 termination 状态，但不返回 TerminationIdPool
        (只在同步环境下使用)

        :return: 包含所有任务的列表
        """
        results: list[TaskEnvelope] = []
        while True:
            try:
                item: TaskEnvelope | TerminationSignal = self.queue.get_nowait()
                self._log_get(item)
                if isinstance(item, TaskEnvelope):
                    results.append(item)
                else:
                    self._record_termination(item)
            except Exception:
                break
        return results


# ==== TaskOutQueue ====
class TaskOutQueue:
    """任务输出队列，将任务广播到一个或多个下游队列通道。"""

    queue_list: list[Any]
    target_names: list[str | None]
    in_name: str
    log_inlet: "LogInlet"
    _name_to_idx: dict[str, int]

    # ==== 初始化 ====
    def __init__(
        self,
        queue_list: list[Any],
        target_names: list[str | None],
        in_name: str,
        log_inlet: "LogInlet",
    ) -> None:
        """
        任务输出队列类，用于管理多个输出队列

        :param queue_list: 输出队列列表，每个元素为一个线程队列或异步队列
        :param target_names: 下游节点名称列表，用于标识每个队列
        :param in_name: 当前节点唯一名称，用于记录日志
        :param log_inlet: 日志记录器，用于记录入队出队日志
        :raises ConfigurationError: 如果队列列表和目标名称列表长度不一致
        """
        if len(queue_list) != len(target_names):
            raise ConfigurationError(
                "queue_list and target_names must have the same length"
            )

        self.queue_list = queue_list
        self.target_names = target_names
        self.in_name = in_name
        self.log_inlet = log_inlet

        self._name_to_idx = {
            name: i for i, name in enumerate(target_names) if name is not None
        }

    # ==== put ====
    def _log_put(self, item: TaskEnvelope | TerminationSignal, idx: int) -> None:
        """
        记录入队日志

        :param item: 入队的任务或终止信号
        :param idx: 输出队列通道的索引
        """
        if isinstance(item, TaskEnvelope):
            t = "task"
        else:
            t = "termination"
        self.log_inlet.put_item(t, item.id, self.in_name, str(self.target_names[idx]))

    def add_queue(self, queue: Any, name: str) -> None:
        """
        添加一个输出队列到队列列表中

        :param queue: 要添加的输出队列
        :param name: 队列的目标节点名称，用于标识该队列
        :raises DuplicateNodeError: 如果名称已存在于队列列表中
        """
        if name in self._name_to_idx:
            raise DuplicateNodeError(f"duplicate queue target name: {name}")
        self._name_to_idx[name] = len(self.queue_list)
        self.queue_list.append(queue)
        self.target_names.append(name)

    def put(self, item: TaskEnvelope | TerminationSignal) -> None:
        """
        入队任务或终止信号到所有输出队列通道

        :param item: 要入队的任务或终止信号
        """
        for index, _ in enumerate(self.queue_list):
            self.put_channel(item, index)

    def put_target(self, item: TaskEnvelope | TerminationSignal, name: str) -> None:
        """
        入队任务或终止信号到指定的输出队列

        :param item: 要入队的任务或终止信号
        :param name: 输出队列目标节点名称，用于标识该队列通道
        """
        self.put_channel(item, self._name_to_idx[name])

    def put_channel(self, item: TaskEnvelope | TerminationSignal, idx: int) -> None:
        """
        入队任务或终止信号到指定的输出队列通道

        :param item: 要入队的任务或终止信号
        :param idx: 输出队列通道的索引
        """
        try:
            self.queue_list[idx].put(item)
            self._log_put(item, idx)
        except Exception as e:
            self.log_inlet.put_item_error(item.source, self.in_name, e)
