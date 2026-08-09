# runtime/core_queue.py
from __future__ import annotations

from queue import Empty, Queue
from typing import Any

from .core_envelope import TaskEnvelope
from .util_errors import (
    DuplicateNodeError,
    TerminationMergeError,
    UnknownNodeError,
)
from .util_types import TerminationIdPool, TerminationSignal


# ==== 输入队列 ====
class TaskInQueue[T]:
    """任务输入队列，聚合多个上游来源的任务和终止信号。"""

    out_name: str
    queue: Queue[TaskEnvelope[T] | TerminationSignal]
    source_names: list[str]
    termination_dict: dict[str, int]

    # ==== 初始化 ====
    def __init__(
        self,
        out_name: str,
        maxsize: int = 0,
    ) -> None:
        """
        初始化任务入队

        :param out_name: 当前节点唯一名称
        :param maxsize: 队列最大容量，默认为 0（无限制）
        """
        self.out_name = out_name
        self.queue = Queue(maxsize=maxsize)

        self.source_names = []
        self.termination_dict = {}

    # ==== 添加 ====

    def add_source_name(self, name: str) -> None:
        """
        添加入队来源名称

        :param name: 入队来源名称
        :raises DuplicateNodeError: 如果名称已存在
        """
        if name in self.source_names:
            raise DuplicateNodeError(f"duplicate queue source name: {name}")
        self.source_names.append(name)

    # ==== 终止 ====
    def _record_termination(self, signal: TerminationSignal) -> None:
        """
        记录入队来源的终止信号

        :param signal: 入队来源的终止信号
        :raises UnknownNodeError: 如果信号来源不在已知来源集合中
        """
        source = signal.source

        valid_sources = set(self.source_names) | {"input"}
        if source not in valid_sources:
            raise UnknownNodeError(f"unknown queue source name: {source}")

        self.termination_dict[source] = signal.id

    def _can_merge_termination(self) -> bool:
        """
        判断是否可以合并普通输入队列的终止信号

        :return: 如果所有来源都已发出终止信号则返回 True，否则返回 False
        """
        return all(name in self.termination_dict for name in self.source_names)

    def _merge_termination(self) -> TerminationIdPool:
        """
        合并所有输入队列的终止信号

        这里只合并来自 source_names 的 termination，不处理：
        - input 注入的直接终止
        - self.out_name 的 merge 后终止

        :return: 合并后的终止信号池
        :raises TerminationMergeError: 如果存在尚未收到终止信号的来源
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

    # ==== 入队与出队 ====
    def put(self, item: TaskEnvelope[T] | TerminationSignal) -> None:
        """
        入队任务或终止信号

        :param item: 要入队的任务或终止信号
        """
        self.queue.put(item)

    def get(self) -> TaskEnvelope[T] | TerminationIdPool:
        """
        出队任务或终止符号id池

        :return: 出队的任务或终止符号id池
        """
        while True:
            item: TaskEnvelope[T] | TerminationSignal | TerminationIdPool = (
                self.queue.get()
            )
            result = self._process_item(item)
            if result is None:
                continue
            return result

    def _process_item(
        self,
        item: TaskEnvelope[T] | TerminationSignal | TerminationIdPool,
    ) -> TaskEnvelope[T] | TerminationIdPool | None:
        """
        处理出队的任务或终止符号

        :param item: 出队的任务或终止信号
        :return: 处理后的任务或终止符号id池
        """
        if isinstance(item, TaskEnvelope):
            return item

        if isinstance(item, TerminationIdPool):
            # 直接注入的终止信号池，不经上游汇合逻辑
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

    def drain(self) -> list[TaskEnvelope[T]]:
        """
        清空队列中的所有任务，返回所有任务列表
        并记录 termination 状态，但不返回 TerminationIdPool
        (只在同步环境下使用)

        :return: 包含所有任务的列表
        """
        results: list[TaskEnvelope[T]] = []
        while True:
            try:
                item: TaskEnvelope[T] | TerminationSignal = self.queue.get_nowait()
                if isinstance(item, TaskEnvelope):
                    results.append(item)
                else:
                    self._record_termination(item)
            except Empty:
                break
        return results


# ==== 输出队列 ====
class TaskOutQueue[T]:
    """任务输出队列，将任务广播到一个或多个下游队列通道。"""

    in_name: str
    _queues: dict[str, Queue[TaskEnvelope[T] | TerminationSignal]]  # name → queue

    # ==== 初始化 ====
    def __init__(
        self,
        in_name: str,
    ) -> None:
        """
        任务输出队列类，用于管理多个输出队列

        :param in_name: 当前节点唯一名称，用于记录日志
        """
        self.in_name = in_name

        self._queues = {}

    # ==== 入队 ====

    def add_queue(self, queue: Any, name: str) -> None:
        """
        添加一个输出队列到队列列表中

        :param queue: 要添加的输出队列
        :param name: 队列的目标节点名称，用于标识该队列
        :raises DuplicateNodeError: 如果名称已存在于队列列表中
        """
        if name in self._queues:
            raise DuplicateNodeError(f"duplicate queue target name: {name}")
        self._queues[name] = queue

    def put(self, item: TaskEnvelope[T] | TerminationSignal) -> None:
        """
        入队任务或终止信号到所有输出队列通道

        :param item: 要入队的任务或终止信号
        """
        for name in self._queues:
            self.put_target(item, name)

    def put_target(self, item: TaskEnvelope[T] | TerminationSignal, name: str) -> None:
        """
        入队任务或终止信号到指定的输出队列

        :param item: 要入队的任务或终止信号
        :param name: 输出队列目标节点名称，用于标识该队列通道
        """
        self._queues[name].put(item)

    # ==== 查询 ====

    def get_target_names(self) -> list[str]:
        """
        获取所有输出队列的目标节点名称

        :return: 输出队列目标节点名称列表
        """
        return list(self._queues.keys())
