import pytest
from test_utils import fibonacci, fibonacci_async

from celestialflow import TaskExecutor


def test_fibonacci_serial():
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        fibonacci,
        execution_mode="serial",
        max_workers=6,
        max_retries=1,
        show_progress=False,
    )
    executor.add_retry_exceptions(ValueError)

    executor.start(test_task_1)


def test_fibonacci_thread():
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        fibonacci,
        execution_mode="thread",
        max_workers=6,
        max_retries=1,
        show_progress=False,
    )
    executor.add_retry_exceptions(ValueError)

    executor.start(test_task_1)

@pytest.mark.asyncio
async def test_fibonacci_async():
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    executor = TaskExecutor(
        fibonacci_async,
        execution_mode="async",
        max_workers=6,
        max_retries=1,
        show_progress=False,
    )
    executor.add_retry_exceptions(ValueError)

    await executor.start_async(test_task_1)


if __name__ == "__main__":
    test_fibonacci_serial()
    pass
