import asyncio
import time

from celestialflow import TaskExecutor, benchmark_executor


def fibonacci(n):
    if n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)


async def fibonacci_async(n):
    if n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        result_0 = await fibonacci_async(n - 1)
        result_1 = await fibonacci_async(n - 2)
        return result_0 + result_1


def sleep_1(_):
    time.sleep(1)


async def sleep_1_async(_):
    await asyncio.sleep(1)


async def bench_executor_fibonacci():
    bench_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(fibonacci, max_workers=6, max_retries=1, show_progress=True)
    executor.add_retry_exceptions(ValueError)

    executor_async = TaskExecutor(
        fibonacci_async, max_workers=6, max_retries=1, show_progress=True
    )
    executor_async.add_retry_exceptions(ValueError)

    sync_modes = ["serial", "thread", "process"]
    async_modes = ["async"]
    await benchmark_executor(
        executor, executor_async, bench_task_1, sync_modes, async_modes
    )


async def bench_executor_sleep():
    task_list = list(range(12))

    executor = TaskExecutor(
        sleep_1,
        max_workers=12,
        max_retries=0,
        show_progress=True,
    )
    executor_async = TaskExecutor(
        sleep_1_async,
        max_workers=12,
        max_retries=0,
        show_progress=True,
    )

    sync_modes = ["serial", "thread", "process"]
    async_modes = ["async"]
    await benchmark_executor(
        executor, executor_async, task_list, sync_modes, async_modes
    )


async def main():
    await bench_executor_fibonacci()
    await bench_executor_sleep()


if __name__ == "__main__":
    asyncio.run(main())
