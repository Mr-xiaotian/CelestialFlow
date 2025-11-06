import pytest, logging
from time import time

from celestialflow import TaskManager, format_table


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
        # 并发执行两个异步递归调用
        result_0 = await fibonacci_async(n - 1)
        result_1 = await fibonacci_async(n - 2)
        return result_0 + result_1


# 测试 TaskManager 的单线程/多线程/多进程任务
def test_manager():
    test_task_0 = range(25, 37)
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]
    test_task_2 = (item for item in test_task_1)

    manager = TaskManager(fibonacci, worker_limit=6, max_retries=1, show_progress=True)
    manager.add_retry_exceptions(ValueError)

    results = manager.test_methods(test_task_1)
    table_results = format_table(*results)
    logging.info("\n" + table_results)


# 测试 TaskManager 的异步任务
@pytest.mark.asyncio
async def test_manager_async():
    test_task_0 = range(25, 37)
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]
    test_task_2 = (item for item in test_task_1)

    manager = TaskManager(
        fibonacci_async, worker_limit=6, max_retries=1, show_progress=True
    )
    manager.add_retry_exceptions(ValueError)
    start = time()
    await manager.start_async(test_task_1)
    logging.info(f"run_in_async: {time() - start}")


if __name__ == "__main__":
    test_manager()
    # test_manager_async()
