import asyncio
import os
import random
from time import sleep
from typing import Any

from celestialflow import (
    TaskGraph,
    TaskSplitter,
    TaskExecutor,
    benchmark_graph,
)


def sleep_1(n: Any) -> Any:
    sleep(1)
    return n


async def async_sleep_1(n: Any) -> Any:
    await asyncio.sleep(1)
    return n


def sleep_random_02(n: Any) -> Any:
    sleep(random.randint(0, 2))
    return n


async def async_sleep_random_02(n: Any) -> Any:
    await asyncio.sleep(random.randint(0, 2))
    return n


def sleep_random_A(n: Any) -> Any:
    return sleep_random_02(n)


def sleep_random_B(n: Any) -> Any:
    return sleep_random_02(n)


def sleep_random_C(n: Any) -> Any:
    return sleep_random_02(n)


def sleep_random_D(n: Any) -> Any:
    return sleep_random_02(n)


def sleep_random_E(n: Any) -> Any:
    return sleep_random_02(n)


def sleep_random_F(n: Any) -> Any:
    return sleep_random_02(n)


async def async_sleep_random_A(n: Any) -> Any:
    return await async_sleep_random_02(n)


async def async_sleep_random_B(n: Any) -> Any:
    return await async_sleep_random_02(n)


async def async_sleep_random_C(n: Any) -> Any:
    return await async_sleep_random_02(n)


async def async_sleep_random_D(n: Any) -> Any:
    return await async_sleep_random_02(n)


async def async_sleep_random_E(n: Any) -> Any:
    return await async_sleep_random_02(n)


async def async_sleep_random_F(n: Any) -> Any:
    return await async_sleep_random_02(n)


def fibonacci(n: Any) -> int:
    if n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1 or n == 2:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)


async def async_fibonacci(n: Any) -> int:
    return fibonacci(n)


def divide_by_two(x: int | float) -> float:
    return x / 2


async def async_divide_by_two(x: int | float) -> float:
    return x / 2


def square(x: int) -> int:
    if x == 317811:
        raise ValueError("Bench error in 317811")
    return x**2


async def async_square(x: int) -> int:
    if x == 317811:
        raise ValueError("Bench error in 317811")
    return x**2


def add_one(x: int) -> int:
    return x + 1


async def async_add_one(x: int) -> int:
    return x + 1


def multiply_two(x: int) -> int:
    return x * 2


async def async_multiply_two(x: int) -> int:
    return x * 2


async def bench_graph_0() -> None:
    node1 = TaskExecutor(
        "NodeA",
        fibonacci,
        max_workers=4,
        max_retries=1,
    )
    node2 = TaskExecutor(
        "NodeB1",
        square,
        max_workers=4,
        max_retries=1,
    )
    node3 = TaskExecutor(
        "NodeB2",
        sleep_1,
        max_workers=4,
    )
    node4 = TaskExecutor(
        "NodeC",
        divide_by_two,
        max_workers=4,
    )

    graph = TaskGraph("bench_graph_0")
    graph.set_nodes(
        nodes=[node1, node2, node3, node4],
    )
    graph.connect([node1], [node2, node3])
    graph.connect([node2], [node4])

    node1.set_retry_exceptions(ValueError)
    node2.set_retry_exceptions(ValueError)

    # async graph
    async_node1 = TaskExecutor("NodeA", async_fibonacci, max_workers=4, max_retries=1)
    async_node2 = TaskExecutor("NodeB1", async_square, max_workers=4, max_retries=1)
    async_node3 = TaskExecutor("NodeB2", async_sleep_1, max_workers=4)
    async_node4 = TaskExecutor("NodeC", async_divide_by_two, max_workers=4)

    async_graph = TaskGraph("bench_graph_0_async")
    async_graph.set_nodes(
        nodes=[async_node1, async_node2, async_node3, async_node4],
    )
    async_graph.connect([async_node1], [async_node2, async_node3])
    async_graph.connect([async_node2], [async_node4])

    async_node1.set_retry_exceptions(ValueError)
    async_node2.set_retry_exceptions(ValueError)

    input_tasks = {
        node1.get_name(): range(25, 32),
        async_node1.get_name(): range(25, 32),
    }

    print("bench_graph_0")
    await benchmark_graph(graph, async_graph, input_tasks)


async def bench_graph_1() -> None:
    A = TaskExecutor("NodeA", sleep_random_A, max_workers=5)
    B = TaskExecutor("NodeB", sleep_random_B, max_workers=5)
    C = TaskExecutor("NodeC", sleep_random_C, max_workers=5)
    D = TaskExecutor("NodeD", sleep_random_D, max_workers=5)
    E = TaskExecutor("NodeE", sleep_random_E, max_workers=5)
    F = TaskExecutor("NodeF", sleep_random_F, max_workers=5)

    graph = TaskGraph("bench_graph_1")
    graph.set_nodes(
        nodes=[A, B, C, D, E, F],
    )
    graph.connect([A], [B, C])
    graph.connect([B], [D, E])
    graph.connect([C], [E])
    graph.connect([D], [F])

    # async graph
    aA = TaskExecutor("NodeA", async_sleep_random_A, max_workers=5)
    aB = TaskExecutor("NodeB", async_sleep_random_B, max_workers=5)
    aC = TaskExecutor("NodeC", async_sleep_random_C, max_workers=5)
    aD = TaskExecutor("NodeD", async_sleep_random_D, max_workers=5)
    aE = TaskExecutor("NodeE", async_sleep_random_E, max_workers=5)
    aF = TaskExecutor("NodeF", async_sleep_random_F, max_workers=5)

    async_graph = TaskGraph("bench_graph_1_async")
    async_graph.set_nodes(
        nodes=[aA, aB, aC, aD, aE, aF],
    )
    async_graph.connect([aA], [aB, aC])
    async_graph.connect([aB], [aD, aE])
    async_graph.connect([aC], [aE])
    async_graph.connect([aD], [aF])

    input_tasks = {
        A.get_name(): range(10),
        aA.get_name(): range(10),
    }

    print("bench_graph_1")
    await benchmark_graph(graph, async_graph, input_tasks)


async def bench_graph_2() -> None:
    S = TaskSplitter("Splitter")
    A = TaskExecutor("NodeA", add_one, max_workers=20)
    B = TaskExecutor("NodeB", multiply_two, max_workers=20)
    C = TaskExecutor("NodeC", multiply_two, max_workers=20)

    graph = TaskGraph("bench_graph_2")
    graph.set_nodes(nodes=[S, A, B, C])
    graph.connect([S], [A])
    graph.connect([A], [B, C])

    aS = TaskSplitter("Splitter")
    aA = TaskExecutor("NodeA", async_add_one, max_workers=20)
    aB = TaskExecutor("NodeB", async_multiply_two, max_workers=20)
    aC = TaskExecutor("NodeC", async_multiply_two, max_workers=20)

    async_graph = TaskGraph("bench_graph_2_async")
    async_graph.set_nodes(nodes=[aS, aA, aB, aC])
    async_graph.connect([aS], [aA])
    async_graph.connect([aA], [aB, aC])

    input_tasks = {
        S.get_name(): [range(10_000)],
        aS.get_name(): [range(10_000)],
    }

    print("bench_graph_2")
    await benchmark_graph(graph, async_graph, input_tasks)


async def main_async() -> None:
    await bench_graph_0()
    await bench_graph_1()
    await bench_graph_2()


if __name__ == "__main__":
    asyncio.run(main_async())
