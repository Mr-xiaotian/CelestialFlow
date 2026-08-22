# benchmark/util_benchmark.py
from __future__ import annotations

import asyncio
import time
from collections.abc import Iterable, Mapping
from typing import Any

from ..graph import TaskGraph
from ..runtime.util_format import format_table
from ..stage import TaskExecutor
from .util_clone import clone_executor, clone_graph

type AnyTaskExecutor = TaskExecutor[Any, Any]


async def benchmark_executor(
    sync_executor: AnyTaskExecutor,
    async_executor: AnyTaskExecutor,
    task_source: Iterable[Any],
    execution_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对执行器进行基准测试

    :param sync_executor: 同步执行器模板（用于 serial/thread execution_mode）
    :param async_executor: 异步执行器模板（用于 async execution_mode）
    :param task_source: 任务源，用于生成任务列表
    :param execution_modes: 执行模式列表，默认 ["serial", "thread", "async"]
    :return: 包含测试结果的字典
    """
    task_list: list[Any] = list(task_source)
    execution_modes = execution_modes or ["serial", "thread", "async"]

    use_time: list[list[float]] = []
    for mode in execution_modes:
        if mode == "async":
            cloned_executor = clone_executor(async_executor)
        else:
            cloned_executor = clone_executor(sync_executor)
        cloned_executor.set_execution_mode(mode)

        start = time.perf_counter()
        if mode == "async":
            await cloned_executor.run_async(task_list)
        else:
            cloned_executor.run(task_list)
        use_time.append([time.perf_counter() - start])

    use_time_table: str = format_table(use_time, execution_modes, ["Time"])
    print(f"Use time:\n{use_time_table}\n")

    return {
        "use_time": use_time,
        "execution_modes": execution_modes,
        "table": use_time_table,
    }


async def benchmark_graph(
    sync_graph: TaskGraph,
    async_graph: TaskGraph,
    init_tasks_dict: Mapping[str, Iterable[Any]],
    graph_modes: list[str] | None = None,
    execution_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对任务图进行基准测试，覆盖 ``graph_mode × execution_mode`` 的全部组合。

    - ``sync_graph`` 用于 ``execution_mode in {"serial", "thread"}`` 的单元格；
    - ``async_graph`` 用于 ``execution_mode == "async"`` 的单元格；
    - ``graph_mode`` 决定当前单元格使用 ``run()`` 还是 ``run_async()`` 启动。

    :param sync_graph: 同步任务图模板（用于 serial/thread execution_mode）
    :param async_graph: 异步任务图模板（用于 async execution_mode）
    :param init_tasks_dict: 初始任务字典，键为任务标签，值为任务列表
    :param graph_modes: 要测试的图执行模式列表，默认包括 "serial", "thread", "async"
    :param execution_modes: 执行模式列表，默认 ["serial", "thread", "async"]
    :return: 包含测试结果的字典
    """
    graph_modes = graph_modes or ["serial", "thread", "async"]
    execution_modes = execution_modes or ["serial", "thread", "async"]

    base_tasks: dict[str, list[Any]] = {
        stage_name: list(tasks) for stage_name, tasks in init_tasks_dict.items()
    }

    test_table_list: list[list[float]] = []

    for graph_mode in graph_modes:
        time_list: list[float] = []

        for execution_mode in execution_modes:
            cloned_graph = (
                clone_graph(async_graph)
                if execution_mode == "async"
                else clone_graph(sync_graph)
            )
            cloned_graph.set_graph_mode(graph_mode)
            cloned_graph.set_stage_execution_mode(execution_mode)

            run_tasks: dict[str, Iterable[Any]] = {
                stage_name: list(tasks) for stage_name, tasks in base_tasks.items()
            }
            start_time = time.perf_counter()
            if graph_mode == "async":
                await cloned_graph.run_async(run_tasks)
            else:
                if execution_mode == "async":
                    await asyncio.to_thread(cloned_graph.run, run_tasks)
                else:
                    cloned_graph.run(run_tasks)
            time_list.append(time.perf_counter() - start_time)

        test_table_list.append(time_list)

    time_table: str = format_table(
        test_table_list,
        graph_modes,
        execution_modes,
        "graph/execution",
    )
    print(f"Time table:\n{time_table}")
    return {
        "use_time": test_table_list,
        "table": time_table,
        "graph_modes": graph_modes,
        "execution_modes": execution_modes,
    }
