import os
import random
from time import sleep

from dotenv import load_dotenv

from celestialflow import TaskGraph, TaskStage, benchmark_graph

load_dotenv()
report_host = os.getenv("REPORT_HOST")
report_port = os.getenv("REPORT_PORT")

ctree_host = os.getenv("CTREE_HOST")
ctree_http_host = os.getenv("CTREE_HTTP_PORT")
ctree_grpc_port = os.getenv("CTREE_GRPC_PORT")


def sleep_1(n):
    sleep(1)
    return n


def sleep_random_02(n):
    sleep(random.randint(0, 2))
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


def divide_by_two(x):
    return x / 2


def square(x):
    if x == 317811:
        raise ValueError("Bench error in 317811")
    return x**2


def bench_graph_0():
    stage1 = TaskStage(
        fibonacci,
        execution_mode="thread",
        max_workers=4,
        max_retries=1,
        show_progress=False,
    )
    stage2 = TaskStage(
        square,
        execution_mode="thread",
        max_workers=4,
        max_retries=1,
        show_progress=False,
    )
    stage3 = TaskStage(
        sleep_1,
        execution_mode="thread",
        max_workers=4,
        show_progress=False,
    )
    stage4 = TaskStage(
        divide_by_two,
        execution_mode="thread",
        max_workers=4,
        show_progress=False,
    )

    stage1.set_graph_context([stage2, stage3], "process", stage_name="stage A")
    stage2.set_graph_context([stage4], "process", stage_name="stage B.1")
    stage3.set_graph_context([], "process", stage_name="stage B.2")
    stage4.set_graph_context([], "process", stage_name="stage C")

    stage1.add_retry_exceptions(ValueError)
    stage2.add_retry_exceptions(ValueError)

    graph = TaskGraph(root_stages=[stage1])
    graph.set_reporter(True, host=report_host, port=report_port)
    graph.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    bench_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    input_tasks = {
        stage1.get_tag(): bench_task_1,
    }
    stage_modes = ["serial", "process"]
    execution_modes = ["serial", "thread"]

    benchmark_graph(graph, input_tasks, stage_modes, execution_modes)


def bench_graph_1():
    A = TaskStage(func=sleep_random_A, execution_mode="thread", max_workers=5)
    B = TaskStage(func=sleep_random_B, execution_mode="serial", max_workers=5)
    C = TaskStage(func=sleep_random_C, execution_mode="serial", max_workers=5)
    D = TaskStage(func=sleep_random_D, execution_mode="thread", max_workers=5)
    E = TaskStage(func=sleep_random_E, execution_mode="thread", max_workers=5)
    F = TaskStage(func=sleep_random_F, execution_mode="serial", max_workers=5)

    A.set_graph_context(next_stages=[B, C], stage_mode="process", stage_name="Stage_A")
    B.set_graph_context(next_stages=[D, E], stage_mode="process", stage_name="Stage_B")
    C.set_graph_context(next_stages=[E], stage_mode="process", stage_name="Stage_C")
    D.set_graph_context(next_stages=[F], stage_mode="process", stage_name="Stage_D")
    E.set_graph_context(next_stages=[], stage_mode="process", stage_name="Stage_E")
    F.set_graph_context(next_stages=[], stage_mode="process", stage_name="Stage_F")

    graph = TaskGraph([A])
    graph.set_reporter(True, host=report_host, port=report_port)
    graph.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    input_tasks = {
        A.get_tag(): range(10),
    }
    stage_modes = ["serial", "process"]
    execution_modes = ["serial", "thread"]

    benchmark_graph(graph, input_tasks, stage_modes, execution_modes)


if __name__ == "__main__":
    bench_graph_1()
