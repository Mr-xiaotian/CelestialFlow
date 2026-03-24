# runtime/core_runner.py
from __future__ import annotations

import asyncio
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from threading import Event, Lock
from typing import TYPE_CHECKING, Any

from . import TaskEnvelope, TaskProgress
from .util_types import TerminationSignal, TerminationIdPool

if TYPE_CHECKING:
    from ..stage.core_executor import TaskExecutor


class TaskRunner:
    def __init__(self, task_executor: TaskExecutor, func, max_workers: int):
        """
        初始化任务运行器

        :param task_executor: 任务执行器
        :param func: 任务函数
        :param max_workers: 工作线程或进程数量限制
        """
        self.task_executor = task_executor
        self.func = func
        self.max_workers = max_workers

        self._pool: ThreadPoolExecutor | ProcessPoolExecutor | None = None

    def init_pool(self, execution_mode: str) -> None:
        """
        初始化线程池或进程池，根据执行模式和当前是否为空来判断是否初始化

        :param execution_mode: 执行模式，"thread" 或 "process"
        """
        # 可以复用的线程池或进程池
        if execution_mode == "thread" and self._pool is None:
            self._pool = ThreadPoolExecutor(max_workers=self.max_workers)
        elif execution_mode == "process" and self._pool is None:
            self._pool = ProcessPoolExecutor(max_workers=self.max_workers)

    def process_termination_signal(
        self, termination_pool: TerminationIdPool
    ) -> TerminationSignal:
        """
        处理终止信号，生成 merge 事件

        :param termination_pool: 包含多个终止信号 ID 的池
        :return: 合并后的终止信号
        """
        parent_ids = termination_pool.ids
        termination_id = self.task_executor.ctree_client.emit(
            "termination.merge",
            parents=parent_ids,
            payload=self.task_executor.get_summary(),
        )
        signal = TerminationSignal(
            termination_id,
            source=self.task_executor.get_tag(),
        )
        self.task_executor.log_sinker.termination_merge(
            self.task_executor.get_func_name(), parent_ids, termination_id
        )
        return signal

    def run_in_serial(self) -> None:
        """
        串行地执行任务
        """
        while True:
            while True:
                envelope = self.task_executor.task_queues.get()
                if isinstance(envelope, TerminationIdPool):
                    termination_signal = self.process_termination_signal(envelope)
                    break

                task, task_hash, _, _ = envelope.unwrap()

                if self.task_executor.metrics.is_duplicate(task_hash):
                    self.task_executor.deal_duplicate(envelope)
                    self.task_executor.task_progress.update(1)
                    continue
                self.task_executor.metrics.add_processed_set(task_hash)
                try:
                    start_time = time.perf_counter()
                    result = self.func(*self.task_executor.get_args(task))
                    self.task_executor.process_task_success(
                        envelope, result, start_time
                    )
                except Exception as error:
                    self.task_executor.handle_task_error(envelope, error)
                self.task_executor.task_progress.update(1)

            self.task_executor.task_queues.reset()

            if self.task_executor.metrics.is_tasks_finished():
                self.task_executor.result_queues.put(termination_signal)
                self.task_executor.task_progress.close()
                return

            self.task_executor.log_sinker._sink(
                "DEBUG", f"{self.task_executor.get_func_name()} is not finished."
            )
            self.task_executor.task_queues.put(termination_signal)

    def run_with_pool(self, execution_mode: str) -> None:
        """
        使用指定的执行池（线程池或进程池）来并行执行任务。

        :param execution_mode: 执行模式，"thread" 或 "process"
        """
        self.init_pool(execution_mode)

        while True:
            task_start_dict = {}  # 用于存储任务开始时间

            # 用于追踪进行中任务数的计数器和事件
            in_flight = 0
            in_flight_lock = Lock()
            all_done_event = Event()
            all_done_event.set()  # 初始为无任务状态，设为完成状态

            def on_task_done(
                future, envelope: TaskEnvelope, task_progress: TaskProgress
            ):
                # 回调函数中处理任务结果
                task_progress.update(1)
                task_id = envelope.id

                try:
                    result = future.result()
                    start_time = task_start_dict.pop(task_id, None)
                    self.task_executor.process_task_success(
                        envelope, result, start_time
                    )
                except Exception as error:
                    task_start_dict.pop(task_id, None)
                    self.task_executor.handle_task_error(envelope, error)
                # 任务完成后减少in_flight计数
                with in_flight_lock:
                    nonlocal in_flight
                    in_flight -= 1
                    if in_flight == 0:
                        all_done_event.set()

            # 从任务队列中提交任务到执行池
            while True:
                envelope = self.task_executor.task_queues.get()
                if isinstance(envelope, TerminationIdPool):
                    termination_signal = self.process_termination_signal(envelope)
                    break

                task, task_hash, task_id, _ = envelope.unwrap()

                if self.task_executor.metrics.is_duplicate(task_hash):
                    self.task_executor.deal_duplicate(envelope)
                    self.task_executor.task_progress.update(1)
                    continue
                self.task_executor.metrics.add_processed_set(task_hash)

                # 提交新任务时增加in_flight计数，并清除完成事件
                with in_flight_lock:
                    in_flight += 1
                    all_done_event.clear()

                task_start_dict[task_id] = time.perf_counter()
                future = self._pool.submit(
                    self.func, *self.task_executor.get_args(task)
                )
                future.add_done_callback(
                    lambda f, t_e=envelope: on_task_done(
                        f, t_e, self.task_executor.task_progress
                    )
                )

            # 等待所有已提交任务完成（包括回调）
            all_done_event.wait()

            # 所有任务和回调都完成了，现在可以安全关闭进度条
            self.task_executor.task_queues.reset()

            if self.task_executor.metrics.is_tasks_finished():
                self.task_executor.result_queues.put(termination_signal)
                self.task_executor.task_progress.close()
                break

            self.task_executor.log_sinker._sink(
                "DEBUG", f"{self.task_executor.get_func_name()} is not finished."
            )
            self.task_executor.task_queues.put(termination_signal)

        self.release_pool()

    def release_pool(self) -> None:
        """
        关闭线程池和进程池，释放资源
        """
        self._pool.shutdown(wait=True)
        self._pool = None

    async def run_in_async(self) -> None:
        """
        异步地执行任务，限制并发数量
        """
        while True:
            semaphore = asyncio.Semaphore(
                self.task_executor.max_workers
            )  # 限制并发数量

            async def sem_task(envelope: TaskEnvelope):
                start_time = time.perf_counter()  # 记录任务开始时间
                async with semaphore:  # 使用信号量限制并发
                    result = await self._run_single_task(envelope.task)
                    return (
                        envelope,
                        result,
                        start_time,
                    )  # 返回 task, result 和 start_time

            # 创建异步任务列表
            async_tasks = []

            while True:
                envelope = await self.task_executor.task_queues.get_async()
                if isinstance(envelope, TerminationIdPool):
                    termination_signal = self.process_termination_signal(envelope)
                    break

                _, task_hash, _, _ = envelope.unwrap()

                if self.task_executor.metrics.is_duplicate(task_hash):
                    self.task_executor.deal_duplicate(envelope)
                    self.task_executor.task_progress.update(1)
                    continue
                self.task_executor.metrics.add_processed_set(task_hash)
                async_tasks.append(sem_task(envelope))  # 使用信号量包裹的任务

            # 并发运行所有任务
            for envelope, result, start_time in await asyncio.gather(
                *async_tasks, return_exceptions=True
            ):
                if not isinstance(result, Exception):
                    await self.task_executor.process_task_success_async(
                        envelope, result, start_time
                    )
                else:
                    await self.task_executor.handle_task_error_async(envelope, result)
                self.task_executor.task_progress.update(1)

            self.task_executor.task_queues.reset()

            if self.task_executor.metrics.is_tasks_finished():
                await self.task_executor.result_queues.put_async(termination_signal)
                self.task_executor.task_progress.close()
                return

            self.task_executor.log_sinker._sink(
                "DEBUG", f"{self.task_executor.get_func_name()} is not finished."
            )
            await self.task_executor.task_queues.put_async(termination_signal)

    async def _run_single_task(self, task: Any) -> Any:
        """
        运行单个任务并捕获异常

        :param task: 要运行的任务
        :return: 任务的结果或异常
        """
        try:
            result = await self.func(*self.task_executor.get_args(task))
            return result
        except Exception as error:
            return error
