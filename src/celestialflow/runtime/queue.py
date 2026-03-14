# runtime/queue.py
from __future__ import annotations

from typing import TYPE_CHECKING, List
from multiprocessing import Queue as MPQueue
from asyncio import Queue as AsyncQueue
from queue import Queue as ThreadQueue, Empty as SyncEmpty

from .envelope import TaskEnvelope
from .types import TerminationSignal

if TYPE_CHECKING:
    from ..persistence import LogSinker


class TaskInQueue:
    def __init__(
        self,
        queue: ThreadQueue | MPQueue | AsyncQueue,
        queue_tags: List[str],
        stage_tag: str,
        log_sinker: "LogSinker",
    ):
        """
        初始化任务入队

        :param queue: 队列对象
        :param queue_tags: 队列标签列表
        :param stage_tag: 任务节点标签
        :param log_sinker: 日志记录器
        """
        self.queue = queue
        self.queue_tags = queue_tags
        self.stage_tag = stage_tag
        self.log_sinker = log_sinker

        self.termination_dict = {}

    def _log_put(self, item):
        """
        记录任务入队日志

        :param item: 入队的任务或终止信号
        """
        if isinstance(item, TaskEnvelope):
            t = "task"
        elif isinstance(item, TerminationSignal):
            t = "termination"
        else:
            t = "unknown"
        self.log_sinker.put_item(t, item.id, item.source, self.stage_tag)

    def _log_get(self, item):
        """
        记录任务出队日志

        :param item: 出队的任务或终止信号
        """
        if isinstance(item, TaskEnvelope):
            t = "task"
        elif isinstance(item, TerminationSignal):
            t = "termination"
        else:
            t = "unknown"
        self.log_sinker.get_item(t, item.id, item.source, self.stage_tag)

    def add_source_tag(self, tag: str):
        """
        添加入队标签

        :param tag: 入队标签
        :raises ValueError: 如果标签已存在
        """
        if tag in self.queue_tags:
            raise ValueError(f"duplicate queue tag: {tag}")
        self.queue_tags.append(tag)

    def reset(self):
        """
        重置任务入队状态
        """
        self.termination_dict = {}

    def _is_all_terminated(self) -> bool:
        """
        判断是否所有入队标签都已收到终止信号

        :return: 如果所有入队标签都已收到终止信号，则返回 True，否则返回 False
        """
        return len(self.termination_dict) == len(self.queue_tags)

    def _merge_termination(self):
        """
        合并所有入队标签的终止信号

        :return: 合并后的终止信号
        """
        return TerminationSignal(
            parents=list(self.termination_dict.values()),
            source=self.stage_tag,
        )

    def _record_termination(self, signal: TerminationSignal):
        """
        记录入队标签的终止信号

        :param signal: 入队标签的终止信号
        """
        self.termination_dict[signal.source] = signal.id

    def put(self, item: TaskEnvelope | TerminationSignal):
        """
        入队任务或终止信号

        :param item: 要入队的任务或终止信号
        """
        try:
            self.queue.put(item)
            self._log_put(item)
        except Exception as e:
            self.log_sinker.put_item_error(item.source, self.stage_tag, e)

    async def put_async(self, item: TaskEnvelope | TerminationSignal):
        """
        异步入队任务或终止信号

        :param item: 要入队的任务或终止信号
        """
        try:
            await self.queue.put(item)
            self._log_put(item)
        except Exception as e:
            self.log_sinker.put_item_error(item.source, self.stage_tag, e)

    def get(self) -> TaskEnvelope | TerminationSignal:
        """
        出队任务或终止信号

        :return: 出队的任务或终止信号
        """
        while True:
            item: TaskEnvelope | TerminationSignal = self.queue.get()
            self._log_get(item)

            if isinstance(item, TaskEnvelope):
                return item

            if isinstance(item, TerminationSignal):
                self._record_termination(item)
                if self._is_all_terminated():
                    return self._merge_termination()
                continue

            raise ValueError(f"unexpected item type: {type(item)}")

    async def get_async(self) -> TaskEnvelope | TerminationSignal:
        """
        异步出队任务或终止信号

        :return: 出队的任务或终止信号
        """
        while True:
            if isinstance(self.queue, AsyncQueue):
                item: TaskEnvelope | TerminationSignal = await self.queue.get()
            else:
                item = self.queue.get()

            self._log_get(item)

            if isinstance(item, TaskEnvelope):
                return item

            if isinstance(item, TerminationSignal):
                self._record_termination(item)
                if self._is_all_terminated():
                    return self._merge_termination()
                continue

            raise ValueError(f"unexpected item type: {type(item)}")

    def drain(self) -> List[TaskEnvelope]:
        """
        清空队列中的所有任务，返回所有任务列表

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
            except SyncEmpty:
                break
            except Exception as e:
                self.log_sinker.get_item_error(item.source, self.stage_tag, exception=e)
                break
        return results


class TaskOutQueue:
    def __init__(
        self,
        queue_list: List[ThreadQueue] | List[MPQueue] | List[AsyncQueue],
        queue_tags: List[str],
        stage_tag: str,
        log_sinker: "LogSinker",
    ):
        """
        任务输出队列类，用于管理多个输出队列

        :param queue_list: 输出队列列表，每个元素为一个线程队列、进程队列或异步队列
        :param queue_tags: 队列标签列表，用于标识每个队列
        :param stage_tag: 任务节点标签，用于记录日志
        :param log_sinker: 日志记录器，用于记录入队出队日志
        :raises ValueError: 如果队列列表和标签列表长度不一致
        """
        if len(queue_list) != len(queue_tags):
            raise ValueError("queue_list and queue_tags must have the same length")

        self.queue_list = queue_list
        self.queue_tags = queue_tags
        self.stage_tag = stage_tag
        self.log_sinker = log_sinker
        self._tag_to_idx = {tag: i for i, tag in enumerate(queue_tags)}

    def _log_put(self, item, idx: int):
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
            t = "unknown"
        self.log_sinker.put_item(t, item.id, self.queue_tags[idx], self.stage_tag)

    def add_queue(self, queue: ThreadQueue | MPQueue | AsyncQueue, tag: str):
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

    def put(self, item: TaskEnvelope | TerminationSignal):
        """
        入队任务或终止信号到所有输出队列通道

        :param item: 要入队的任务或终止信号
        """
        for index, _ in enumerate(self.queue_list):
            self.put_channel(item, index)

    async def put_async(self, item: TaskEnvelope | TerminationSignal):
        """
        异步入队任务或终止信号到所有输出队列通道

        :param item: 要入队的任务或终止信号
        """
        for index, _ in enumerate(self.queue_list):
            await self.put_channel_async(item, index)

    def put_target(self, item: TaskEnvelope | TerminationSignal, tag: str):
        """
        入队任务或终止信号到指定的输出队列标签

        :param item: 要入队的任务或终止信号
        :param tag: 输出队列标签，用于标识该队列通道
        """
        self.put_channel(item, self._tag_to_idx[tag])

    def put_channel(self, item: TaskEnvelope | TerminationSignal, idx: int):
        """
        入队任务或终止信号到指定的输出队列通道

        :param item: 要入队的任务或终止信号
        :param idx: 输出队列通道的索引
        """
        try:
            self.queue_list[idx].put(item)
            self._log_put(item, idx)
        except Exception as e:
            self.log_sinker.put_item_error(
                item.source, self.stage_tag, e
            )

    async def put_channel_async(self, item: TaskEnvelope | TerminationSignal, idx: int):
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
            self.log_sinker.put_item_error(
                item.source, self.stage_tag, e
            )
