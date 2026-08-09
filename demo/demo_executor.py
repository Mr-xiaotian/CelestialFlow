import asyncio
from typing import Any

from demo_utils import fibonacci, fibonacci_async

from celestialflow import TaskExecutor, TaskProgress


def demo_fibonacci_serial() -> None:
    test_task_1: list[Any] = [*list(range(25, 32)), 0, 27, None, 0, ""]

    executor = TaskExecutor(
        "FibonacciSerial",
        fibonacci,
        execution_mode="serial",
        max_workers=6,
        max_retries=1,
    )
    executor.set_retry_exceptions(ValueError)
    executor.add_observer(TaskProgress())

    executor.put_tasks(test_task_1)
    executor.start()


def demo_fibonacci_thread() -> None:
    test_task_1: list[Any] = [*list(range(25, 32)), 0, 27, None, 0, ""]

    executor = TaskExecutor(
        "FibonacciThread",
        fibonacci,
        execution_mode="thread",
        max_workers=6,
        max_retries=1,
    )
    executor.set_retry_exceptions(ValueError)
    executor.add_observer(TaskProgress())

    executor.put_tasks(test_task_1)
    executor.start()


async def demo_fibonacci_async() -> None:
    test_task_1: list[Any] = [*list(range(25, 32)), 0, 27, None, 0, ""]

    executor = TaskExecutor(
        "FibonacciAsync",
        fibonacci_async,
        execution_mode="async",
        max_workers=6,
        max_retries=1,
    )
    executor.set_retry_exceptions(ValueError)
    executor.add_observer(TaskProgress())

    executor.put_tasks(test_task_1)
    await executor.start_async()


if __name__ == "__main__":
    demo_fibonacci_serial()
    demo_fibonacci_thread()
    asyncio.run(demo_fibonacci_async())
