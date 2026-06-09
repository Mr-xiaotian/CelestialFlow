import asyncio
import time
from typing import Any

from celestialflow import TaskExecutor, TaskProgress, benchmark_executor


def fibonacci(n: Any) -> int:
    """同步版斐波那契 — 迭代 O(n)，与 fibonacci_async 算法一致（公平对比）"""
    if not isinstance(n, int):
        raise TypeError("n must be an integer")
    elif n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        prev, curr = 1, 1
        for _ in range(3, n + 1):
            prev, curr = curr, prev + curr
        return curr


async def fibonacci_async(n: Any) -> int:
    if not isinstance(n, int):
        raise TypeError("n must be an integer")
    elif n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        prev, curr = 1, 1
        for i in range(3, n + 1):
            prev, curr = curr, prev + curr
            if i % 8 == 0:
                await asyncio.sleep(0)
        return curr


def sleep_1(_: Any) -> None:
    time.sleep(1)


async def sleep_1_async(_: Any) -> None:
    await asyncio.sleep(1)


async def bench_executor_fibonacci() -> None:
    bench_task_1: list[Any] = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        "fibonacciExecutor",
        fibonacci,
        max_workers=6,
        max_retries=1,
        # log_level="TRACE",
    )
    executor.add_retry_exceptions(ValueError)
    executor.add_observer(TaskProgress())

    executor_async = TaskExecutor(
        "fibonacciExecutorAsync",
        fibonacci_async,
        max_workers=6,
        max_retries=1,
        # log_level="TRACE",
    )
    executor_async.add_retry_exceptions(ValueError)
    executor_async.add_observer(TaskProgress())

    sync_modes = ["serial", "thread"]
    async_modes = ["async"]
    await benchmark_executor(
        executor, executor_async, bench_task_1, sync_modes, async_modes
    )


async def bench_executor_sleep() -> None:
    task_list = list(range(6))

    executor = TaskExecutor(
        "sleepExecutor",
        sleep_1,
        max_workers=6,
        max_retries=0,
        # log_level="TRACE",
    )
    executor.add_observer(TaskProgress())
    executor_async = TaskExecutor(
        "sleepExecutorAsync",
        sleep_1_async,
        max_workers=6,
        max_retries=0,
        # log_level="TRACE",
    )
    executor_async.add_observer(TaskProgress())

    sync_modes = ["serial", "thread"]
    async_modes = ["async"]
    await benchmark_executor(
        executor, executor_async, task_list, sync_modes, async_modes
    )


async def main() -> None:
    await bench_executor_fibonacci()
    await bench_executor_sleep()


if __name__ == "__main__":
    asyncio.run(main())
