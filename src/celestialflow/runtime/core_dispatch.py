# runtime/core_dispatch.py
from __future__ import annotations

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import TYPE_CHECKING

from .core_envelope import TaskEnvelope
from .util_types import TerminationIdPool, TerminationSignal

if TYPE_CHECKING:
    from ..stage.core_executor import TaskExecutor


class TaskDispatch:
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

        self._pool: ThreadPoolExecutor | None = None

    def _init_pool(self, execution_mode: str) -> None:
        """
        初始化线程池，根据执行模式和当前是否为空来判断是否初始化

        :param execution_mode: 执行模式，"thread"
        """
        # 可以复用的线程池
        if execution_mode == "thread" and self._pool is None:
            self._pool = ThreadPoolExecutor(max_workers=self.max_workers)

    def _process_termination_signal(
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
        self.task_executor.log_inlet.termination_merge(
            self.task_executor.get_func_name(), parent_ids, termination_id
        )
        return signal
    
    def _check_and_mark_task(self, task_envelope: TaskEnvelope) -> bool:
        """
        在进入 worker 前完成去重检查

        :param task_envelope: 包含任务信息的信封
        :return: 是否命中重复任务
        """
        _, task_hash, _ = task_envelope.unwrap()

        if self.task_executor.metrics.is_duplicate(task_hash):
            self.task_executor.deal_duplicate(task_envelope)
            return True
        return False

    def _worker(self, task_envelope: TaskEnvelope) -> None:
        """
        同步执行单个任务（计时、成功/失败处理）

        :param task_envelope: 包含任务信息的信封
        """
        task, _, _ = task_envelope.unwrap()
        max_retries = self.task_executor.max_retries

        for retry_time in range(max_retries + 1):
            try:
                start_time = time.perf_counter()
                result = self.func(*self.task_executor.get_args(task))
                self.task_executor.process_task_success(
                    task_envelope, result, start_time
                )
                return
            except Exception as exception:
                if (
                    retry_time >= max_retries
                    or not isinstance(
                        exception, self.task_executor.metrics.retry_exceptions
                    )
                ):
                    self.task_executor.handle_task_fail(task_envelope, exception)
                    return
                task_envelope = self.task_executor.emit_retry_envelope(
                    task_envelope, exception, retry_time + 1
                )

    async def _async_worker(self, task_envelope: TaskEnvelope) -> None:
        """
        异步执行单个任务（计时、成功/失败处理）

        :param task_envelope: 包含任务信息的信封
        """
        task, _, _ = task_envelope.unwrap()
        max_retries = self.task_executor.max_retries

        for retry_time in range(max_retries + 1):
            try:
                start_time = time.perf_counter()
                result = await self.func(*self.task_executor.get_args(task))
                await self.task_executor.process_task_success_async(
                    task_envelope, result, start_time
                )
                return
            except Exception as exception:
                if (
                    retry_time >= max_retries
                    or not isinstance(
                        exception, self.task_executor.metrics.retry_exceptions
                    )
                ):
                    self.task_executor.handle_task_fail(task_envelope, exception)
                    return
                task_envelope = self.task_executor.emit_retry_envelope(
                    task_envelope, exception, retry_time + 1
                )

    def run_in_serial(self) -> None:
        """
        串行地执行任务
        """
        task_queues = self.task_executor.task_queues
        result_queues = self.task_executor.result_queues

        while True:
            while True:
                envelope = task_queues.get()
                if isinstance(envelope, TerminationIdPool):
                    termination_signal = self._process_termination_signal(envelope)
                    break
                if self._check_and_mark_task(envelope):
                    continue

                self._worker(envelope)

            task_queues.reset()

            if self.task_executor.metrics.is_tasks_finished():
                result_queues.put(termination_signal)
                return

            self.task_executor.log_inlet._funnel(
                "DEBUG", f"{self.task_executor.get_func_name()} is not finished."
            )
            task_queues.put(termination_signal)

    def run_in_thread(self) -> None:
        """
        使用指定的线程池来并行执行任务。
        """
        self._init_pool(execution_mode="thread")
        task_queues = self.task_executor.task_queues
        result_queues = self.task_executor.result_queues

        while True:
            futures = [] # 用于存储线程池提交的任务

            while True:
                envelope = task_queues.get()
                if isinstance(envelope, TerminationIdPool):
                    termination_signal = self._process_termination_signal(envelope)
                    break
                if self._check_and_mark_task(envelope):
                    continue

                if self._pool is None:
                    raise RuntimeError("execution pool has not been initialized")
                futures.append(self._pool.submit(self._worker, envelope))

            # 等待当前批次的所有任务完成
            for future in futures:
                future.result()

            task_queues.reset()

            if self.task_executor.metrics.is_tasks_finished():
                result_queues.put(termination_signal)
                break

            self.task_executor.log_inlet._funnel(
                "DEBUG", f"{self.task_executor.get_func_name()} is not finished."
            )
            task_queues.put(termination_signal)

        self._release_pool()

    def _release_pool(self) -> None:
        """
        关闭线程池，释放资源
        """
        if self._pool is not None:
            self._pool.shutdown(wait=True)
        self._pool = None

    async def run_in_async(self) -> None:
        """
        异步地执行任务，限制并发数量
        """
        task_queues = self.task_executor.task_queues
        result_queues = self.task_executor.result_queues

        while True:
            semaphore = asyncio.Semaphore(self.max_workers)

            async def sem_worker(envelope: TaskEnvelope):
                async with semaphore:
                    await self._async_worker(envelope)

            async_tasks = []

            while True:
                envelope = await task_queues.get_async()
                if isinstance(envelope, TerminationIdPool):
                    termination_signal = self._process_termination_signal(envelope)
                    break
                if self._check_and_mark_task(envelope):
                    continue

                async_tasks.append(sem_worker(envelope))

            await asyncio.gather(*async_tasks)

            task_queues.reset()

            if self.task_executor.metrics.is_tasks_finished():
                await result_queues.put_async(termination_signal)
                return

            self.task_executor.log_inlet._funnel(
                "DEBUG", f"{self.task_executor.get_func_name()} is not finished."
            )
            await task_queues.put_async(termination_signal)
