import pytest, logging, pprint, os
import random
from time import sleep
from dotenv import load_dotenv

from celestialflow import TaskStage, TaskGraph, format_table


load_dotenv()
report_host = os.getenv("REPORT_HOST")
report_port = os.getenv("REPORT_PORT")
ctree_host = os.getenv("CTREE_HOST")
ctree_port = os.getenv("CTREE_PORT")


def sleep_1(n):
    sleep(1)
    return n


def sleep_random_02(n):
    sleep(random.randint(0, 2))
    return n


def sleep_random_46(n):
    sleep(random.randint(4, 6))
    return n


def sleep_random_A(n):
    return sleep_random_02(n)


def sleep_random_B(n):
    return sleep_random_02(n)


def sleep_random_C(n):
    return sleep_random_02(n)


def sleep_random_D(n):
    return sleep_random_02(n)


def sleep_random_E(n):
    return sleep_random_02(n)


def sleep_random_F(n):
    return sleep_random_02(n)


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


def add_one(x):
    return x + 1


def subtract_one(x):
    return x - 1


def multiply_by_two(x):
    return x * 2


def divide_by_two(x):
    return x / 2


def square(x):
    if x == 317811:
        raise ValueError("Test error in 317811")
    return x**2


def square_root(x):
    return x**0.5


# 测试 TaskGraph 的功能
def test_graph_0():
    # 定义多个阶段的 TaskStage 实例
    stage1 = TaskStage(
        fibonacci,
        execution_mode="thread",
        worker_limit=4,
        max_retries=1,
        show_progress=False,
    )
    stage2 = TaskStage(
        square,
        execution_mode="thread",
        worker_limit=4,
        max_retries=1,
        show_progress=False,
    )
    stage3 = TaskStage(
        sleep_1,
        execution_mode="thread",
        worker_limit=4,
        show_progress=False,
    )
    stage4 = TaskStage(
        divide_by_two,
        execution_mode="thread",
        worker_limit=4,
        show_progress=False,
    )

    stage1.set_graph_context([stage2, stage3], "process", stage_name="stage A")
    stage2.set_graph_context([stage4], "process", stage_name="stage B.1")
    stage3.set_graph_context([], "process", stage_name="stage B.2")
    stage4.set_graph_context([], "process", stage_name="stage C")

    stage1.add_retry_exceptions(ValueError)
    stage2.add_retry_exceptions(ValueError)

    # 初始化 TaskGraph
    graph = TaskGraph(root_stages=[stage1])
    graph.set_reporter(True, host=report_host, port=report_port)
    graph.set_ctree(True, host=ctree_host, port=ctree_port)

    # 要测试的任务列表
    test_task_0 = range(25, 37)
    test_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]
    # test_task_2 = (item for item in test_task_1)

    input_tasks = {
        stage1.get_tag(): test_task_1,
    }
    stage_modes = ["serial", "process"]
    execution_modes = ["serial", "thread"]

    # 开始任务链
    result = graph.test_methods(input_tasks, stage_modes, execution_modes)
    result["Time table"] = format_table(*result["Time table"])
    for key, value in result.items():
        if isinstance(value, dict):
            value = pprint.pformat(value)
        logging.info(f"{key}: \n{value}")


def test_graph_1():
    # 定义任务节点
    A = TaskStage(func=sleep_random_A, execution_mode="thread")
    B = TaskStage(func=sleep_random_B, execution_mode="serial")
    C = TaskStage(func=sleep_random_C, execution_mode="serial")
    D = TaskStage(func=sleep_random_D, execution_mode="thread")
    E = TaskStage(func=sleep_random_E, execution_mode="thread")
    F = TaskStage(func=sleep_random_F, execution_mode="serial")

    # 设置链式上下文
    A.set_graph_context(next_stages=[B, C], stage_mode="process", stage_name="Stage_A")
    B.set_graph_context(next_stages=[D, E], stage_mode="process", stage_name="Stage_B")
    C.set_graph_context(next_stages=[E], stage_mode="process", stage_name="Stage_C")
    D.set_graph_context(next_stages=[F], stage_mode="process", stage_name="Stage_D")
    E.set_graph_context(next_stages=[], stage_mode="process", stage_name="Stage_E")
    F.set_graph_context(next_stages=[], stage_mode="process", stage_name="Stage_F")

    # 初始化 TaskGraph, 并设置根节点
    graph = TaskGraph([A])
    graph.set_reporter(True, host=report_host, port=report_port)
    # graph.set_ctree(True, host=ctree_host, port=ctree_port)

    input_tasks = {
        A.get_tag(): range(10),
    }
    stage_modes = ["serial", "process"]
    execution_modes = ["serial", "thread"]

    # 开始任务链
    result = graph.test_methods(input_tasks, stage_modes, execution_modes)
    result["Time table"] = format_table(*result["Time table"])
    for key, value in result.items():
        if isinstance(value, dict):
            value = pprint.pformat(value)
        logging.info(f"{key}: \n{value}")


# 在主函数或脚本中调用此函数，而不是在测试中
if __name__ == "__main__":
    test_graph_0()
    # test_graph_1()
    pass
