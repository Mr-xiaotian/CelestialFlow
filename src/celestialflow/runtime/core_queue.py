# runtime/core_queue.py
from __future__ import annotations

from asyncio import Queue as AsyncQueue
from typing import TYPE_CHECKING, Any

from .core_envelope import TaskEnvelope
from .util_types import TerminationIdPool, TerminationSignal

if TYPE_CHECKING:
    from ..persistence import LogInlet


class TaskInQueue:
    def __init__(
        self,
        queue: Any,
        queue_tags: list[str],
        out_tag: str,
        log_inlet: "LogInlet",
    ) -> None:
        """
        初始化任务入队

        :param queue: 队列对象
        :param queue_tags: 队列标签列表
        :param out_tag: 任务节点标签
        :param log_inlet: 日志记录器
        """
        self.queue: Any = queue
        self.queue_tags = list(queue_tags)
        self.out_tag = out_tag
        self.log_inlet = log_inlet

        self.termination_dict: dict[str, int] = {}

    def _log_put(self, item: TaskEnvelope | TerminationSignal) -> None:
        """
        记录任务入队日志

        :param item: 入队的任务或终止信号
        """
        if isinstance(item, TaskEnvelope):
            t = "task"
        elif isinstance(item, TerminationSignal):
            t = "termination"
        else:
            raise ValueError(f"unexpected item type: {type(item)}")
        self.log_inlet.put_item(t, item.id, item.source, self.out_tag)

    def _log_get(self, item: TaskEnvelope | TerminationSignal) -> None:
        """
        记录任务出队日志

        :param item: 出队的任务或终止信号
        """
        if isinstance(item, TaskEnvelope):
            t = "task"
        elif isinstance(item, TerminationSignal):
            t = "termination"
        self.log_inlet.get_item(t, item.id, item.source, self.out_tag)

    def add_source_tag(self, tag: str) -> None:
        """
        添加入队标签

        :param tag: 入队标签
        :raises ValueError: 如果标签已存在
        """
        if tag in self.queue_tags:
            raise ValueError(f"duplicate queue tag: {tag}")
        self.queue_tags.append(tag)

    def reset(self) -> None:
        """
        重置任务入队状态
        """
        self.termination_dict = {}

    def _record_termination(self, signal: TerminationSignal) -> None:
        """
        记录入队标签的终止信号

        :param signal: 入队标签的终止信号
        """
        source = signal.source

        valid_sources = set(self.queue_tags) | {"input", self.out_tag}
        if source not in valid_sources:
            raise ValueError(f"unknown queue tag: {source}")

        self.termination_dict[source] = signal.id

    def _can_merge_termination(self) -> bool:
        """
        判断是否可以合并普通输入队列的终止信号
        """
        return all(tag in self.termination_dict for tag in self.queue_tags)

    def _merge_termination(self) -> TerminationIdPool:
        """
        合并所有输入队列的终止信号

        这里只合并来自 queue_tags 的 termination，不处理：
        - input 注入的直接终止
        - self.out_tag 的 merge 后终止

        :return: 合并后的终止信号池
        """
        missing_tags = [
            tag for tag in self.queue_tags if tag not in self.termination_dict
        ]
        if missing_tags:
            raise ValueError(
                f"cannot merge termination, missing queue tags: {missing_tags}"
            )

        return TerminationIdPool(
            ids=[self.termination_dict[tag] for tag in self.queue_tags]
        )

    def put(self, item: TaskEnvelope | TerminationSignal) -> None:
        """
        入队任务或终止信号

        :param item: 要入队的任务或终止信号
        """
        try:
            self.queue.put(item)
            self._log_put(item)
        except Exception as e:
            self.log_inlet.put_item_error(item.source, self.out_tag, e)

    async def put_async(self, item: TaskEnvelope | TerminationSignal) -> None:
        """
        异步入队任务或终止信号

        :param item: 要入队的任务或终止信号
        """
        try:
            await self.queue.put(item)
            self._log_put(item)
        except Exception as e:
            self.log_inlet.put_item_error(item.source, self.out_tag, e)

    def get(self) -> TaskEnvelope | TerminationIdPool:
        """
        出队任务或终止符号id池

        :return: 出队的任务或终止符号id池
        """
        while True:
            item: TaskEnvelope | TerminationSignal = self.queue.get()
            result = self._deal_get_item(item)
            if result is not None:
                return result

    async def get_async(self) -> TaskEnvelope | TerminationIdPool:
        """
        异步出队任务或终止符号id池

        :return: 出队的任务或终止符号id池
        """
        while True:
            item: TaskEnvelope | TerminationSignal = await self.queue.get()
            result = self._deal_get_item(item)
            if result is not None:
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

        if isinstance(item, TerminationSignal):
            self._record_termination(item)
            if "input" in self.termination_dict:
                return TerminationIdPool(ids=[self.termination_dict["input"]])
            elif self.out_tag in self.termination_dict:
                return TerminationIdPool(ids=[self.termination_dict[self.out_tag]])
            elif self._can_merge_termination():
                return self._merge_termination()
            # 信号已记录但尚未集齐所有上游，继续等待
            return None

        raise ValueError(f"unexpected item type: {type(item)}")

    def drain(self) -> list[TaskEnvelope]:
        """
        清空队列中的所有任务，返回所有任务列表
        并记录 termination 状态，但不返回 TerminationIdPool
        (只在同步环境下使用)

        :return: 包含所有任务的列表
        """
        results = []
        while True:
            try:
                item: TaskEnvelope | TerminationSignal = self.queue.get_nowait()
                self._log_get(item)
                if isinstance(item, TaskEnvelope):
                    results.append(item)
                elif isinstance(item, TerminationSignal):
                    self._record_termination(item)
            except Exception:
                break
        return results


class TaskOutQueue:
    def __init__(
        self,
        queue_list: list[Any],
        queue_tags: list[str | None],
        in_tag: str,
        log_inlet: "LogInlet",
    ) -> None:
        """
        任务输出队列类，用于管理多个输出队列

        :param queue_list: 输出队列列表，每个元素为一个线程队列、进程队列或异步队列
        :param queue_tags: 队列标签列表，用于标识每个队列
        :param in_tag: 任务节点标签，用于记录日志
        :param log_inlet: 日志记录器，用于记录入队出队日志
        :raises ValueError: 如果队列列表和标签列表长度不一致
        """
        if len(queue_list) != len(queue_tags):
            raise ValueError("queue_list and queue_tags must have the same length")

        self.queue_list = queue_list
        self.queue_tags = queue_tags
        self.in_tag = in_tag
        self.log_inlet = log_inlet

        self._tag_to_idx = {
            tag: i for i, tag in enumerate(queue_tags) if tag is not None
        }

    def _log_put(self, item: TaskEnvelope | TerminationSignal, idx: int) -> None:
        """
        记录入队日志

        :param item: 入队的任务或终止信号
        :param idx: 输出队列通道的索引
        """
        if isinstance(item, TaskEnvelope):
            t = "task"
        elif isinstance(item, TerminationSignal):
            t = "termination"
        else:
            raise ValueError(f"unexpected item type: {type(item)}")
        self.log_inlet.put_item(t, item.id, self.in_tag, str(self.queue_tags[idx]))

    def add_queue(self, queue: Any, tag: str) -> None:
        """
        添加一个输出队列到队列列表中

        :param queue: 要添加的输出队列
        :param tag: 队列的标签，用于标识该队列
        :raises ValueError: 如果标签已存在于队列列表中
        """
        if tag in self._tag_to_idx:
            raise ValueError(f"duplicate queue tag: {tag}")
        self._tag_to_idx[tag] = len(self.queue_list)
        self.queue_list.append(queue)
        self.queue_tags.append(tag)

    def put(self, item: TaskEnvelope | TerminationSignal) -> None:
        """
        入队任务或终止信号到所有输出队列通道

        :param item: 要入队的任务或终止信号
        """
        for index, _ in enumerate(self.queue_list):
            self.put_channel(item, index)

    async def put_async(self, item: TaskEnvelope | TerminationSignal) -> None:
        """
        异步入队任务或终止信号到所有输出队列通道

        :param item: 要入队的任务或终止信号
        """
        for index, _ in enumerate(self.queue_list):
            await self.put_channel_async(item, index)

    def put_target(self, item: TaskEnvelope | TerminationSignal, tag: str) -> None:
        """
        入队任务或终止信号到指定的输出队列标签

        :param item: 要入队的任务或终止信号
        :param tag: 输出队列标签，用于标识该队列通道
        """
        self.put_channel(item, self._tag_to_idx[tag])

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
            self.log_inlet.put_item_error(item.source, self.in_tag, e)

    async def put_channel_async(
        self, item: TaskEnvelope | TerminationSignal, idx: int
    ) -> None:
        """
        异步入队任务或终止信号到指定的输出队列通道

        :param item: 要入队的任务或终止信号
        :param idx: 输出队列通道的索引
        """
        try:
            if isinstance(self.queue_list[idx], AsyncQueue):
                await self.queue_list[idx].put(item)
            else:
                self.queue_list[idx].put(item)
            self._log_put(item, idx)
        except Exception as e:
            self.log_inlet.put_item_error(item.source, self.in_tag, e)
