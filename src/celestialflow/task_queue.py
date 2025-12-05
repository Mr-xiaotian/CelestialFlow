from __future__ import annotations

import asyncio, time
from typing import List
from asyncio import Queue as AsyncQueue, QueueEmpty as AsyncEmpty
from multiprocessing import Queue as MPQueue
from queue import Queue as ThreadQueue, Empty as SyncEmpty

from .task_types import TerminationSignal, TERMINATION_SIGNAL
from .task_logging import TaskLogger


class TaskQueue:
    def __init__(
        self,
        queue_list: List[ThreadQueue | MPQueue | AsyncQueue],
        queue_tag: List[str],
        logger_queue: ThreadQueue | MPQueue,
        stage_tag: str,
        direction: str,
    ):
        if len(queue_list) != len(queue_tag):
            raise ValueError("queue_list and queue_tag must have the same length")

        self.queue_list = queue_list
        self.queue_tag = queue_tag
        self.task_logger = TaskLogger(logger_queue)
        self.stage_tag = stage_tag
        self.direction = direction

        self.current_index = 0  # 记录起始队列索引，用于轮询
        self.terminated_queue_set = set()

    def add_queue(self, queue: ThreadQueue | MPQueue | AsyncQueue, tag: str):
        self.queue_list.append(queue)
        self.queue_tag.append(tag)

    def reset(self):
        self.current_index = 0
        self.terminated_queue_set.clear()

    def put(self, source):
        """
        将结果放入所有结果队列

        :param source: 任务结果
        """
        for queue, queue_tag in zip(self.queue_list, self.queue_tag):
            queue.put(source)
            self.task_logger.put_source(source, queue_tag, self.stage_tag, self.direction)

    async def put_async(self, source):
        """
        将结果放入所有结果队列(async模式)

        :param source: 任务结果
        """
        for queue, queue_tag in zip(self.queue_list, self.queue_tag):
            await queue.put(source)
            self.task_logger.put_source(source, queue_tag, self.stage_tag, self.direction)

    def put_first(self, source):
        """
        将结果放入第一个结果队列

        :param source: 任务结果
        """
        self.queue_list[0].put(source)
        self.task_logger.put_source(source, self.queue_tag[0], self.stage_tag, self.direction)

    async def put_first_async(self, source):
        """
        将结果放入第一个结果队列(async模式)

        :param source: 任务结果
        """
        await self.queue_list[0].put(source)
        self.task_logger.put_source(source, self.queue_tag[0], self.stage_tag, self.direction)

    def get(self, poll_interval: float = 0.01) -> object:
        """
        从多个队列中轮询获取任务。

        :param poll_interval: 每轮遍历后的等待时间（秒）
        :return: 获取到的任务，或 TerminationSignal 表示所有队列已终止
        """
        total_queues = len(self.queue_list)

        if total_queues == 1:
            # ✅ 只有一个队列时，使用阻塞式 get，提高效率
            queue = self.queue_list[0]
            source = queue.get()  # 阻塞等待，无需 sleep    
            self.task_logger.get_source(source, self.queue_tag[0], self.stage_tag)

            if isinstance(source, TerminationSignal):
                self.terminated_queue_set.add(0)
                return TERMINATION_SIGNAL
            return source

        while True:
            for i in range(total_queues):
                idx = (self.current_index + i) % total_queues  # 轮转访问
                if idx in self.terminated_queue_set:
                    continue

                queue = self.queue_list[idx]
                try:
                    source = queue.get_nowait()
                    self.task_logger.get_source(source, self.queue_tag[idx], self.stage_tag)

                    if isinstance(source, TerminationSignal):
                        self.terminated_queue_set.add(idx)
                        continue
                    
                    self.current_index = (
                        idx + 1
                    ) % total_queues  # 下一轮从下一个队列开始
                    return source
                except SyncEmpty:
                    continue
                except Exception as e:
                    self.task_logger._log(
                        "WARNING",
                        f"Error get from Edge({self.queue_tag[idx]} -> {self.stage_tag}): {type(e).__name__}({e})",
                    )
                    continue

            # 所有队列都终止了
            if len(self.terminated_queue_set) == total_queues:
                return TERMINATION_SIGNAL

            # 所有队列都暂时无数据，避免 busy-wait
            time.sleep(poll_interval)

    async def get_async(self, poll_interval=0.01) -> object:
        """
        异步轮询多个 AsyncQueue，获取任务。

        :param poll_interval: 全部为空时的 sleep 间隔（秒）
        :return: task 或 TerminationSignal
        """
        total_queues = len(self.queue_list)

        if total_queues == 1:
            # ✅ 单队列直接 await 阻塞等待
            queue = self.queue_list[0]
            source = await queue.get()
            self.task_logger.get_source(source, self.queue_tag[0], self.stage_tag)

            if isinstance(source, TerminationSignal):
                self.terminated_queue_set.add(0)
                return TERMINATION_SIGNAL
            
            return source

        while True:
            for i in range(total_queues):
                idx = (self.current_index + i) % total_queues
                if idx in self.terminated_queue_set:
                    continue

                queue = self.queue_list[idx]
                try:
                    source = queue.get_nowait()
                    self.task_logger.get_source(source, self.queue_tag[idx], self.stage_tag)

                    if isinstance(source, TerminationSignal):
                        self.terminated_queue_set.add(idx)
                        continue

                    self.current_index = (idx + 1) % total_queues
                    return source
                except AsyncEmpty:
                    continue
                except Exception as e:
                    self.task_logger._log(
                        "WARNING",
                        f"Error get from Edge({self.queue_tag[idx]} -> {self.stage_tag}): {type(e).__name__}({e})",
                    )
                    continue

            if len(self.terminated_queue_set) == total_queues:
                return TERMINATION_SIGNAL

            await asyncio.sleep(poll_interval)
