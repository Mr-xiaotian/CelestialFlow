from __future__ import annotations

import asyncio, time
from typing import TYPE_CHECKING, List
from multiprocessing import Queue as MPQueue
from asyncio import Queue as AsyncQueue, QueueEmpty as AsyncEmpty
from queue import Queue as ThreadQueue, Empty as SyncEmpty

from celestialtree import (
    Client as CelestialTreeClient,
)

from .task_errors import InvalidOptionError
from .task_types import TaskEnvelope, TerminationSignal
from .task_logger import TaskLogger

if TYPE_CHECKING:
    from .task_stage import TaskStage


class TaskQueue:
    def __init__(
        self,
        queue_list: List[ThreadQueue] | List[MPQueue] | List[AsyncQueue],
        queue_tags: List[str],
        direction: str,
        stage: TaskStage,
        task_logger: TaskLogger,
        ctree_client: CelestialTreeClient,
    ):
        if len(queue_list) != len(queue_tags):
            raise ValueError("queue_list and queue_tags must have the same length")

        valid_dirextions = ("in", "out")
        if direction not in valid_dirextions:
            raise InvalidOptionError("direction", direction, valid_dirextions)

        self.queue_list = queue_list
        self.queue_tags = queue_tags
        self.direction = direction

        self.stage_tag = stage.get_tag()
        self.stage_summary = stage.get_summary()
        self.task_logger = task_logger
        self.ctree_client = ctree_client

        self.current_index = 0  # 记录起始队列索引，用于轮询
        self.termination_dict = {}

        self._tag_to_idx = {tag: i for i, tag in enumerate(queue_tags)}

    def set_ctree(self, ctree_client):
        self.ctree_client = ctree_client

    def _merge_termination_single(self, idx: int, item_id: str) -> TerminationSignal:
        self.termination_dict[idx] = item_id
        termination_id = self.ctree_client.emit(
            "termination.merge",
            parents=[item_id],
            payload=self.stage_summary,
        )
        return TerminationSignal(termination_id)

    def _merge_all_terminations(self) -> TerminationSignal:
        termination_id = self.ctree_client.emit(
            "termination.merge",
            parents=list(self.termination_dict.values()),
            payload=self.stage_summary,
        )
        return TerminationSignal(termination_id)

    def _log_put(self, item, idx: int):
        if isinstance(item, TaskEnvelope):
            t = "task"
        elif isinstance(item, TerminationSignal):
            t = "termination"
        else:
            t = "unknown"
        self.task_logger.put_item(
            t, item.id, self.queue_tags[idx], self.stage_tag, self.direction
        )

    def _log_get(self, item, idx: int):
        if isinstance(item, TaskEnvelope):
            t = "task"
        elif isinstance(item, TerminationSignal):
            t = "termination"
        else:
            t = "unknown"
        self.task_logger.get_item(t, item.id, self.queue_tags[idx], self.stage_tag)

    def get_tag_idx(self, tag: str) -> int:
        return self._tag_to_idx[tag]

    def add_queue(self, queue: ThreadQueue | MPQueue | AsyncQueue, tag: str):
        if tag in self._tag_to_idx:
            raise ValueError(f"duplicate queue tag: {tag}")
        self._tag_to_idx[tag] = len(self.queue_list)
        self.queue_list.append(queue)
        self.queue_tags.append(tag)

    def reset(self):
        self.current_index = 0
        self.termination_dict = {}

    def is_empty(self) -> bool:
        return all(queue.empty() for queue in self.queue_list)

    def put(self, item: TaskEnvelope | TerminationSignal):
        """
        将结果放入所有结果队列

        :param item: 任务或终止符
        """
        for index, _ in enumerate(self.queue_list):
            self.put_channel(item, index)

    async def put_async(self, item: TaskEnvelope | TerminationSignal):
        """
        将结果放入所有结果队列(async模式)

        :param item: 任务或终止符
        """
        for index, _ in enumerate(self.queue_list):
            await self.put_channel_async(item, index)

    def put_first(self, item: TaskEnvelope | TerminationSignal):
        """
        将结果放入第一个结果队列

        :param item: 任务或终止符
        """
        self.put_channel(item, 0)

    async def put_first_async(self, item: TaskEnvelope | TerminationSignal):
        """
        将结果放入第一个结果队列(async模式)

        :param item: 任务或终止符
        """
        await self.put_channel_async(item, 0)

    def put_target(self, item: TaskEnvelope | TerminationSignal, tag: str):
        """
        将结果放入指定结果队列

        :param item: 任务或终止符
        :param tag: 队列标签
        """
        self.put_channel(item, self.get_tag_idx(tag))

    async def put_target_async(self, item: TaskEnvelope | TerminationSignal, tag: str):
        """
        将结果放入指定结果队列(async模式)

        :param item: 任务或终止符
        :param tag: 队列标签
        """
        await self.put_channel_async(item, self.get_tag_idx(tag))

    def put_channel(self, item, idx: int):
        """
        将结果放入指定队列

        :param item: 任务或终止符
        :param idx: 队列索引
        """
        try:
            self.queue_list[idx].put(item)
            self._log_put(item, idx)
        except Exception as e:
            self.task_logger.put_item_error(
                self.queue_tags[idx], self.stage_tag, self.direction, e
            )

    async def put_channel_async(self, item, idx: int):
        """
        将结果放入指定队列(async模式)

        :param item: 任务或终止符
        :param idx: 队列索引
        """
        try:
            await self.queue_list[idx].put(item)
            self._log_put(item, idx)
        except Exception as e:
            self.task_logger.put_item_error(
                self.queue_tags[idx], self.stage_tag, self.direction, e
            )

    def _try_get_from_idx(
        self, idx: int, empty_exc
    ) -> TaskEnvelope | None:
        if idx in self.termination_dict:
            return None

        queue = self.queue_list[idx]
        try:
            item = queue.get_nowait()
            self._log_get(item, idx)

            if isinstance(item, TerminationSignal):
                self.termination_dict[idx] = item.id
                return None

            if isinstance(item, TaskEnvelope):
                self.current_index = (idx + 1) % len(self.queue_list)
                return item

            return None
        except empty_exc:
            return None
        except Exception as e:
            self.task_logger.get_item_error(
                self.queue_tags[idx], self.stage_tag, exception=e
            )
            return None

    def get(self, poll_interval: float = 0.01) -> TaskEnvelope | TerminationSignal:
        """
        从多个队列中轮询获取任务。

        :param poll_interval: 每轮遍历后的等待时间（秒）
        :return: 获取到的任务，或 TerminationSignal 表示所有队列已终止
        """
        total_queues = len(self.queue_list)

        if total_queues == 1:
            queue = self.queue_list[0]
            item: TaskEnvelope | TerminationSignal = queue.get()
            self._log_get(item, 0)

            if isinstance(item, TerminationSignal):
                return self._merge_termination_single(0, item.id)

            return item

        while True:
            for i in range(total_queues):
                idx = (self.current_index + i) % total_queues
                item = self._try_get_from_idx(idx, SyncEmpty)
                if isinstance(item, TaskEnvelope):
                    return item

            if len(self.termination_dict) == total_queues:
                return self._merge_all_terminations()

            time.sleep(poll_interval)

    async def get_async(self, poll_interval=0.01) -> TaskEnvelope | TerminationSignal:
        """
        异步轮询多个 AsyncQueue，获取任务。

        :param poll_interval: 全部为空时的 sleep 间隔（秒）
        :return: task 或 TerminationSignal
        """
        total_queues = len(self.queue_list)

        if total_queues == 1:
            queue = self.queue_list[0]
            item: TaskEnvelope | TerminationSignal = await queue.get()
            self._log_get(item, 0)

            if isinstance(item, TerminationSignal):
                return self._merge_termination_single(0, item.id)

            return item

        while True:
            for i in range(total_queues):
                idx = (self.current_index + i) % total_queues
                item = self._try_get_from_idx(idx, AsyncEmpty)
                if isinstance(item, TaskEnvelope):
                    return item

            if len(self.termination_dict) == total_queues:
                return self._merge_all_terminations()

            await asyncio.sleep(poll_interval)

    def drain(self) -> List[TaskEnvelope]:
        """提取所有队列中当前剩余的 item（非阻塞）。"""
        results = []
        total_queues = len(self.queue_list)

        for idx in range(total_queues):
            if idx in self.termination_dict:
                continue

            queue = self.queue_list[idx]
            while True:
                try:
                    item: TaskEnvelope | TerminationSignal = queue.get_nowait()
                    self._log_get(item, idx)

                    if isinstance(item, TerminationSignal):
                        self.termination_dict[idx] = item.id
                        break

                    elif isinstance(item, TaskEnvelope):
                        results.append(item)

                except SyncEmpty:
                    break
                except Exception as e:
                    self.task_logger.get_item_error(
                        self.queue_tags[idx],
                        self.stage_tag,
                        self.direction,
                        exception=e,
                    )
                    break

        return results
