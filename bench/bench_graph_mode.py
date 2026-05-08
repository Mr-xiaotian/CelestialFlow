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
        "StageA",
        fibonacci,
        max_workers=4,
        max_retries=1,
    )
    stage2 = TaskStage(
        "StageB1",
        square,
        max_workers=4,
        max_retries=1,
    )
    stage3 = TaskStage(
        "StageB2",
        sleep_1,
        max_workers=4,
    )
    stage4 = TaskStage(
        "StageC",
        divide_by_two,
        max_workers=4,
    )

    graph = TaskGraph()
    graph.set_stages(
        root_stages=[stage1],
        stages=[stage1, stage2, stage3, stage4],
    )
    graph.connect([stage1], [stage2, stage3])
    graph.connect([stage2], [stage4])

    stage1.add_retry_exceptions(ValueError)
    stage2.add_retry_exceptions(ValueError)

    graph.set_reporter(True, host=report_host, port=report_port)
    graph.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    bench_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    input_tasks = {
        stage1.get_tag(): bench_task_1,
    }
    stage_modes = ["serial", "thread", "process"]
    execution_modes = ["serial", "thread"]

    benchmark_graph(graph, input_tasks, stage_modes, execution_modes)


def bench_graph_1():
    A = TaskStage(
        "StageA",
        sleep_random_A,
        max_workers=5,
    )
    B = TaskStage(
        "StageB",
        sleep_random_B,
        max_workers=5,
    )
    C = TaskStage(
        "StageC",
        sleep_random_C,
        max_workers=5,
    )
    D = TaskStage(
        "StageD",
        sleep_random_D,
        max_workers=5,
    )
    E = TaskStage(
        "StageE",
        sleep_random_E,
        max_workers=5,
    )
    F = TaskStage(
        "StageF",
        sleep_random_F,
        max_workers=5,
    )

    graph = TaskGraph()
    graph.set_stages(
        root_stages=[A],
        stages=[A, B, C, D, E, F],
    )
    graph.connect([A], [B, C])
    graph.connect([B], [D, E])
    graph.connect([C], [E])
    graph.connect([D], [F])

    graph.set_reporter(True, host=report_host, port=report_port)
    graph.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    input_tasks = {
        A.get_tag(): range(10),
    }
    stage_modes = ["serial", "thread", "process"]
    execution_modes = ["serial", "thread"]

    benchmark_graph(graph, input_tasks, stage_modes, execution_modes)


if __name__ == "__main__":
    bench_graph_1()
