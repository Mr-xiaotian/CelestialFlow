import asyncio

from demo_utils import fibonacci, fibonacci_async

from celestialflow import TaskExecutor, TaskProgress


def demo_fibonacci_serial():
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        "FibonacciSerial",
        fibonacci,
        execution_mode="serial",
        max_workers=6,
        max_retries=1,

    )
    executor.add_retry_exceptions(ValueError)
    executor.add_observer(TaskProgress())

    executor.start(test_task_1)


def demo_fibonacci_thread():
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        "FibonacciThread",
        fibonacci,
        execution_mode="thread",
        max_workers=6,
        max_retries=1,

    )
    executor.add_retry_exceptions(ValueError)
    executor.add_observer(TaskProgress())

    executor.start(test_task_1)


async def demo_fibonacci_async():
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        "FibonacciAsync",
        fibonacci_async,
        execution_mode="async",
        max_workers=6,
        max_retries=1,

    )
    executor.add_retry_exceptions(ValueError)
    executor.add_observer(TaskProgress())

    await executor.start_async(test_task_1)


if __name__ == "__main__":
    demo_fibonacci_serial()
    demo_fibonacci_thread()
    asyncio.run(demo_fibonacci_async())
