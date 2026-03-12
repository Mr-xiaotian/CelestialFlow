import time
import asyncio

from celestialflow import TaskExecutor, format_table, benchmark_executor


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


def test_executor_fibonacci():
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        fibonacci, worker_limit=6, max_retries=1, show_progress=True
    )
    executor.add_retry_exceptions(ValueError)

    execution_modes = ["serial", "thread", "process"]
    benchmark_executor(executor, test_task_1, execution_modes)


async def test_executor_fibonacci_async():
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        fibonacci_async, worker_limit=6, max_retries=1, show_progress=True
    )
    executor.add_retry_exceptions(ValueError)
    start = time.time()
    await executor.start_async(test_task_1)
    print(f"run_in_async: {time.time() - start}")


def test_executor_sleep():
    executor = TaskExecutor(
        sleep_1,
        worker_limit=12,
        max_retries=0,
        show_progress=True,
    )
    tasks = list(range(12))

    execution_modes = ["serial", "thread", "process"]
    benchmark_executor(executor, tasks, execution_modes)


async def test_executor_sleep_async():
    executor = TaskExecutor(
        sleep_1_async,
        worker_limit=12,
        max_retries=0,
        show_progress=True,
    )
    tasks = list(range(12))

    start = time.time()
    await executor.start_async(tasks)
    print(f"run_in_async: {time.time() - start}")


async def main():
    test_executor_fibonacci()
    await test_executor_fibonacci_async()
    test_executor_sleep()
    await test_executor_sleep_async()


if __name__ == "__main__":
    asyncio.run(main())