import asyncio
import os
import random
from time import sleep

from dotenv import load_dotenv

from celestialflow import TaskGraph, TaskStage, benchmark_graph

load_dotenv()
report_host = os.getenv("REPORT_HOST", "127.0.0.1")
report_port = int(os.getenv("REPORT_PORT", "5000"))


def sleep_1(n):
    sleep(1)
    return n


async def async_sleep_1(n):
    await asyncio.sleep(1)
    return n


def sleep_random_02(n):
    sleep(random.randint(0, 2))
    return n


async def async_sleep_random_02(n):
    await asyncio.sleep(random.randint(0, 2))
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


async def async_sleep_random_A(n):
    return await async_sleep_random_02(n)


async def async_sleep_random_B(n):
    return await async_sleep_random_02(n)


async def async_sleep_random_C(n):
    return await async_sleep_random_02(n)


async def async_sleep_random_D(n):
    return await async_sleep_random_02(n)


async def async_sleep_random_E(n):
    return await async_sleep_random_02(n)


async def async_sleep_random_F(n):
    return await async_sleep_random_02(n)


def fibonacci(n):
    if n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)


async def async_fibonacci(n):
    return fibonacci(n)


def divide_by_two(x):
    return x / 2


async def async_divide_by_two(x):
    return x / 2


def square(x):
    if x == 317811:
        raise ValueError("Bench error in 317811")
    return x**2


async def async_square(x):
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

    # async graph
    async_stage1 = TaskStage("StageA", async_fibonacci, max_workers=4, max_retries=1)
    async_stage2 = TaskStage("StageB1", async_square, max_workers=4, max_retries=1)
    async_stage3 = TaskStage("StageB2", async_sleep_1, max_workers=4)
    async_stage4 = TaskStage("StageC", async_divide_by_two, max_workers=4)

    async_graph = TaskGraph()
    async_graph.set_stages(
        root_stages=[async_stage1],
        stages=[async_stage1, async_stage2, async_stage3, async_stage4],
    )
    async_graph.connect([async_stage1], [async_stage2, async_stage3])
    async_graph.connect([async_stage2], [async_stage4])

    async_stage1.add_retry_exceptions(ValueError)
    async_stage2.add_retry_exceptions(ValueError)

    graph.set_reporter(True, host=report_host, port=report_port)
    async_graph.set_reporter(True, host=report_host, port=report_port)

    bench_task_1 = list(range(25, 32)) + [0, 27, None, 0, ""]

    input_tasks = {
        stage1.get_tag(): bench_task_1,
        async_stage1.get_tag(): bench_task_1,
    }

    benchmark_graph(graph, async_graph, input_tasks)


def bench_graph_1():
    A = TaskStage("StageA", sleep_random_A, max_workers=5)
    B = TaskStage("StageB", sleep_random_B, max_workers=5)
    C = TaskStage("StageC", sleep_random_C, max_workers=5)
    D = TaskStage("StageD", sleep_random_D, max_workers=5)
    E = TaskStage("StageE", sleep_random_E, max_workers=5)
    F = TaskStage("StageF", sleep_random_F, max_workers=5)

    graph = TaskGraph()
    graph.set_stages(
        root_stages=[A],
        stages=[A, B, C, D, E, F],
    )
    graph.connect([A], [B, C])
    graph.connect([B], [D, E])
    graph.connect([C], [E])
    graph.connect([D], [F])

    # async graph
    aA = TaskStage("StageA", async_sleep_random_A, max_workers=5)
    aB = TaskStage("StageB", async_sleep_random_B, max_workers=5)
    aC = TaskStage("StageC", async_sleep_random_C, max_workers=5)
    aD = TaskStage("StageD", async_sleep_random_D, max_workers=5)
    aE = TaskStage("StageE", async_sleep_random_E, max_workers=5)
    aF = TaskStage("StageF", async_sleep_random_F, max_workers=5)

    async_graph = TaskGraph()
    async_graph.set_stages(
        root_stages=[aA],
        stages=[aA, aB, aC, aD, aE, aF],
    )
    async_graph.connect([aA], [aB, aC])
    async_graph.connect([aB], [aD, aE])
    async_graph.connect([aC], [aE])
    async_graph.connect([aD], [aF])

    graph.set_reporter(True, host=report_host, port=report_port)
    async_graph.set_reporter(True, host=report_host, port=report_port)

    input_tasks = {
        A.get_tag(): range(10),
        aA.get_tag(): range(10),
    }

    benchmark_graph(graph, async_graph, input_tasks)


if __name__ == "__main__":
    bench_graph_0()
    bench_graph_1()
