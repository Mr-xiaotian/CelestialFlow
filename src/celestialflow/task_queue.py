from __future__ import annotations

import asyncio, time
from typing import List
from asyncio import Queue as AsyncQueue, QueueEmpty
from multiprocessing import Queue as MPQueue
from queue import Queue as ThreadQueue, Empty

from .task_types import TerminationSignal, TERMINATION_SIGNAL
from .task_logging import TaskLogger

class TaskQueue:
    def __init__(self, queue_list: List[ThreadQueue | MPQueue | AsyncQueue], logger_queue: ThreadQueue | MPQueue, stage_tag: str):
        self.queue_list = queue_list
        self.task_logger = TaskLogger(logger_queue)
        self.stage_tag = stage_tag

        self.current_index = 0
        self.terminated_queue_set = set()

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
            item = queue.get()  # 阻塞等待，无需 sleep
            if isinstance(item, TerminationSignal):
                self.terminated_queue_set.add(0)
                self.task_logger._log("TRACE", f"queue[0](only) terminated in {self.stage_tag}")
                return TERMINATION_SIGNAL
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
                        self.task_logger._log(
                            "TRACE", f"queue[{idx}] terminated in {self.stage_tag}"
                        )
                        continue
                    self.current_index = (
                        idx + 1
                    ) % total_queues  # 下一轮从下一个队列开始
                    return item
                except Empty:
                    continue
                except Exception as e:
                    self.task_logger._log(
                        "WARNING",
                        f"Error from queue[{idx}]: {type(e).__name__}({e}) in {self.stage_tag}",
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
            task = await queue.get()
            if isinstance(task, TerminationSignal):
                self.terminated_queue_set.add(0)
                self.task_logger._log(
                    "TRACE", "get_queue_list_async: queue[0] terminated"
                )
                return TERMINATION_SIGNAL
            return task

        while True:
            for i in range(total_queues):
                idx = (self.current_index + i) % total_queues
                if idx in self.terminated_queue_set:
                    continue
                queue = self.queue_list[idx]
                try:
                    task = queue.get_nowait()
                    if isinstance(task, TerminationSignal):
                        self.terminated_queue_set.add(idx)
                        self.task_logger._log(
                            "TRACE", f"get_queue_list_async: queue[{idx}] terminated"
                        )
                        continue
                    self.current_index = (idx + 1) % total_queues
                    return task
                except QueueEmpty:
                    continue
                except Exception as e:
                    self.task_logger._log(
                        "WARNING",
                        f"get_queue_list_async: queue[{idx}] error: {type(e).__name__}({e})",
                    )
                    continue

            if len(self.terminated_queue_set) == total_queues:
                return TERMINATION_SIGNAL

            await asyncio.sleep(poll_interval)

    def put(self, result):
        """
        将结果放入所有结果队列

        :param result: 任务结果
        """
        for result_queue in self.queue_list:
            result_queue.put(result)

    async def put_async(self, result):
        """
        将结果放入所有结果队列(async模式)

        :param result: 任务结果
        """
        for queue in self.queue_list:
            await queue.put(result)


    
