import pytest
import time
import asyncio

from celestialflow import TaskExecutor


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


def test_fibonacci_serial():
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        fibonacci, execution_mode="serial", worker_limit=6, max_retries=1, show_progress=False
    )
    executor.add_retry_exceptions(ValueError)

    executor.start(test_task_1)


def test_fibonacci_thread():
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        fibonacci, execution_mode="thread", worker_limit=6, max_retries=1, show_progress=False
    )
    executor.add_retry_exceptions(ValueError)

    executor.start(test_task_1)


def test_fibonacci_process():
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        fibonacci, execution_mode="process", worker_limit=6, max_retries=1, show_progress=False
    )
    executor.add_retry_exceptions(ValueError)

    executor.start(test_task_1)


@pytest.mark.asyncio
async def test_fibonacci_async():
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        fibonacci_async, execution_mode="async", worker_limit=6, max_retries=1, show_progress=False
    )
    executor.add_retry_exceptions(ValueError)

    await executor.start_async(test_task_1)


if __name__ == "__main__":
    test_fibonacci_serial()
    pass