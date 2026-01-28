from __future__ import annotations

import asyncio, time
from typing import List
from asyncio import Queue as AsyncQueue, QueueEmpty as AsyncEmpty
from multiprocessing import Queue as MPQueue
from queue import Queue as ThreadQueue, Empty as SyncEmpty

from .task_types import TaskEnvelope, TerminationSignal, TERMINATION_SIGNAL
from .task_logging import TaskLogger


class TaskQueue:
    def __init__(
        self,
        queue_list: List[ThreadQueue] | List[MPQueue] | List[AsyncQueue],
        queue_tags: List[str],
        log_queue: ThreadQueue | MPQueue,
        log_level: str,
        stage_tag: str,
        direction: str,
    ):
        if len(queue_list) != len(queue_tags):
            raise ValueError("queue_list and queue_tags must have the same length")
        if direction not in ["in", "out"]:
            raise ValueError("direction must be 'in' or 'out'")

        self.queue_list = queue_list
        self.queue_tags = queue_tags
        self.task_logger = TaskLogger(log_queue, log_level)
        self.stage_tag = stage_tag
        self.direction = direction

        self.current_index = 0  # 记录起始队列索引，用于轮询
        self.terminated_queue_set = set()

    def get_tag_idx(self, tag: str) -> int:
        return self.queue_tags.index(tag)

    def add_queue(self, queue: ThreadQueue | MPQueue | AsyncQueue, tag: str):
        self.queue_list.append(queue)
        self.queue_tags.append(tag)

    def reset(self):
        self.current_index = 0
        self.terminated_queue_set.clear()

    def is_empty(self) -> bool:
        return all([queue.empty() for queue in self.queue_list])

    def put(self, item: TaskEnvelope | TerminationSignal):
        """
        将结果放入所有结果队列

        :param item: 任务或终止符
        """
        for index in range(len(self.queue_list)):
            self.put_channel(item, index)

    async def put_async(self, item: TaskEnvelope | TerminationSignal):
        """
        将结果放入所有结果队列(async模式)

        :param item: 任务或终止符
        """
        for index in range(len(self.queue_list)):
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

    def put_channel(self, item: TaskEnvelope | TerminationSignal, channel_index: int):
        """
        将结果放入指定队列

        :param item: 任务或终止符
        :param channel_index: 队列索引
        """
        try:
            self.queue_list[channel_index].put(item)
            if isinstance(item, TaskEnvelope):
                self.task_logger.put_item(
                    "task",
                    item.id,
                    self.queue_tags[channel_index],
                    self.stage_tag,
                    self.direction,
                )
            elif isinstance(item, TerminationSignal):
                self.task_logger.put_item(
                    "termination",
                    item.id,
                    self.queue_tags[channel_index],
                    self.stage_tag,
                    self.direction,
                )

        except Exception as e:
            self.task_logger.put_item_error(
                self.queue_tags[channel_index], self.stage_tag, self.direction, e
            )

    async def put_channel_async(
        self, item: TaskEnvelope | TerminationSignal, channel_index: int
    ):
        """
        将结果放入指定队列(async模式)

        :param item: 任务或终止符
        :param channel_index: 队列索引
        """
        try:
            await self.queue_list[channel_index].put(item)
            if isinstance(item, TaskEnvelope):
                self.task_logger.put_item(
                    "task",
                    item.id,
                    self.queue_tags[channel_index],
                    self.stage_tag,
                    self.direction,
                )
            elif isinstance(item, TerminationSignal):
                self.task_logger.put_item(
                    "termination",
                    item.id,
                    self.queue_tags[channel_index],
                    self.stage_tag,
                    self.direction,
                )

        except Exception as e:
            self.task_logger.put_item_error(
                self.queue_tags[channel_index], self.stage_tag, self.direction, e
            )

    def get(self, poll_interval: float = 0.01) -> TaskEnvelope | TerminationSignal:
        """
        从多个队列中轮询获取任务。

        :param poll_interval: 每轮遍历后的等待时间（秒）
        :return: 获取到的任务，或 TerminationSignal 表示所有队列已终止
        """
        total_queues = len(self.queue_list)

        if total_queues == 1:
            # 只有一个队列时，使用阻塞式 get，提高效率
            queue = self.queue_list[0]
            item: TaskEnvelope | TerminationSignal = queue.get()  # 阻塞等待，无需 sleep

            if isinstance(item, TerminationSignal):
                self.terminated_queue_set.add(0)
                self.task_logger.get_item(
                    "termination", item.id, self.queue_tags[0], self.stage_tag
                )
            else:
                self.task_logger.get_item(
                    "task", item.id, self.queue_tags[0], self.stage_tag
                )

            return item

        while True:
            for i in range(total_queues):
                idx = (self.current_index + i) % total_queues  # 轮转访问
                if idx in self.terminated_queue_set:
                    continue

                queue = self.queue_list[idx]
                try:
                    item = queue.get_nowait()

                    if isinstance(item, TerminationSignal):
                        self.terminated_queue_set.add(idx)
                        self.task_logger.get_item(
                            "termination", item.id, self.queue_tags[idx], self.stage_tag
                        )
                        continue

                    self.task_logger.get_item(
                        "task", item.id, self.queue_tags[idx], self.stage_tag
                    )
                    self.current_index = (idx + 1) % total_queues
                    return item
                except SyncEmpty:
                    continue
                except Exception as e:
                    self.task_logger.get_item_error(
                        self.queue_tags[idx], self.stage_tag, exception=e
                    )
                    continue

            # 所有队列都终止了
            if len(self.terminated_queue_set) == total_queues:
                return TERMINATION_SIGNAL

            # 所有队列都暂时无数据，避免 busy-wait
            time.sleep(poll_interval)

    async def get_async(self, poll_interval=0.01) -> TaskEnvelope | TerminationSignal:
        """
        异步轮询多个 AsyncQueue，获取任务。

        :param poll_interval: 全部为空时的 sleep 间隔（秒）
        :return: task 或 TerminationSignal
        """
        total_queues = len(self.queue_list)

        if total_queues == 1:
            # 单队列直接 await 阻塞等待
            queue = self.queue_list[0]
            item: TaskEnvelope | TerminationSignal = await queue.get()

            if isinstance(item, TerminationSignal):
                self.terminated_queue_set.add(0)
                self.task_logger.get_item(
                    "termination", item.id, self.queue_tags[0], self.stage_tag
                )
            else:
                self.task_logger.get_item(
                    "task", item.id, self.queue_tags[0], self.stage_tag
                )

            return item

        while True:
            for i in range(total_queues):
                idx = (self.current_index + i) % total_queues
                if idx in self.terminated_queue_set:
                    continue

                queue = self.queue_list[idx]
                try:
                    item: TaskEnvelope | TerminationSignal = queue.get_nowait()

                    if isinstance(item, TerminationSignal):
                        self.terminated_queue_set.add(idx)
                        self.task_logger.get_item(
                            "termination", item.id, self.queue_tags[idx], self.stage_tag
                        )
                        continue

                    self.task_logger.get_item(
                        "task", item.id, self.queue_tags[idx], self.stage_tag
                    )
                    self.current_index = (idx + 1) % total_queues
                    return item
                except AsyncEmpty:
                    continue
                except Exception as e:
                    self.task_logger.get_item_error(
                        self.queue_tags[idx], self.stage_tag, exception=e
                    )
                    continue

            if len(self.terminated_queue_set) == total_queues:
                return TERMINATION_SIGNAL

            await asyncio.sleep(poll_interval)

    def drain(self) -> List[TaskEnvelope]:
        """提取所有队列中当前剩余的 item（非阻塞）。"""
        results = []
        total_queues = len(self.queue_list)

        for idx in range(total_queues):
            if idx in self.terminated_queue_set:
                continue

            queue = self.queue_list[idx]
            while True:
                try:
                    item: TaskEnvelope | TerminationSignal = queue.get_nowait()

                    if isinstance(item, TerminationSignal):
                        self.terminated_queue_set.add(idx)
                        self.task_logger.get_item(
                            "termination", item.id, self.queue_tags[idx], self.stage_tag
                        )
                        break

                    self.task_logger.get_item(
                        "task", item.id, self.queue_tags[idx], self.stage_tag
                    )
                    results.append(item)
                except (SyncEmpty, AsyncEmpty):
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
