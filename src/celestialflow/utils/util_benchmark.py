# utils/util_benchmark.py
from __future__ import annotations

import time
from collections.abc import Iterable, Mapping
from typing import Any

from ..graph import TaskGraph
from ..stage import TaskExecutor
from .util_clone import clone_executor, clone_graph
from .util_format import format_table


async def benchmark_executor(
    sync_executor: TaskExecutor,
    async_executor: TaskExecutor,
    task_source: Iterable[Any],
    sync_modes: list[str] | None = None,
    async_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对执行器进行基准测试

    :param sync_executor: 同步执行器
    :param async_executor: 异步执行器
    :param task_source: 任务源，用于生成任务列表
    :param sync_modes: 同步执行模式列表，默认 ["serial", "thread"]
    :param async_modes: 异步执行模式列表，默认 ["async"]
    :return: 包含测试结果的字典
    """
    task_list: list[Any] = list(task_source)
    sync_modes = sync_modes or ["serial", "thread"]
    async_modes = async_modes or ["async"]

    use_time: list[list[float]] = []
    results: list[list[tuple[Any, Any]]] = []
    for mode in sync_modes:
        cloned_executor: TaskExecutor = clone_executor(sync_executor)
        cloned_executor.set_execution_mode(mode)

        start: float = time.perf_counter()
        cloned_executor.start(task_list)
        use_time.append([time.perf_counter() - start])
        results.append(cloned_executor.get_success_pairs())

    for mode in async_modes:
        cloned_executor = clone_executor(async_executor)
        cloned_executor.set_execution_mode(mode)

        start = time.perf_counter()
        await cloned_executor.start_async(task_list)
        use_time.append([time.perf_counter() - start])
        results.append(cloned_executor.get_success_pairs())

    use_time_table: str = format_table(use_time, sync_modes + async_modes, ["Time"])
    results_table: str = format_table(results, sync_modes + async_modes, [])

    print(f"Use time:\n{use_time_table}\n")
    print(f"Results:\n{results_table}\n")

    return {
        "use_time": use_time,
        "sync_modes": sync_modes,
        "async_modes": async_modes,
        "table": use_time_table,
    }


def benchmark_graph(
    sync_graph: TaskGraph,
    async_graph: TaskGraph,
    init_tasks_dict: Mapping[str, Iterable[Any]],
    stage_modes: list[str] | None = None,
    execution_sync_modes: list[str] | None = None,
    execution_async_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对任务图进行基准测试

    :param sync_graph: 同步任务图（用于 serial/thread 模式）
    :param async_graph: 异步任务图（用于 async 模式）
    :param init_tasks_dict: 初始任务字典，键为任务标签，值为任务列表
    :param stage_modes: 要测试的节点执行模式列表，默认包括 "serial", "thread"
    :param execution_sync_modes: 同步执行模式列表，默认 ["serial", "thread"]
    :param execution_async_modes: 异步执行模式列表，默认 ["async"]
    :return: 包含测试结果的字典
    """
    stage_modes = stage_modes or ["serial", "thread"]
    sync_modes = execution_sync_modes or ["serial", "thread"]
    async_modes = execution_async_modes or ["async"]

    base_tasks: dict[str, list[Any]] = {
        tag: list(tasks) for tag, tasks in init_tasks_dict.items()
    }
    execution_modes: list[str] = sync_modes + async_modes

    test_table_list: list[list[float]] = []

    for stage_mode in stage_modes:
        time_list: list[float] = []
        for execution_mode in sync_modes:
            cloned_graph: TaskGraph = clone_graph(sync_graph)
            cloned_graph.set_graph_mode(stage_mode, execution_mode)

            run_tasks: dict[str, list[Any]] = {
                tag: list(tasks) for tag, tasks in base_tasks.items()
            }
            start_time: float = time.perf_counter()
            cloned_graph.start_graph(run_tasks)
            time_list.append(time.perf_counter() - start_time)

        for execution_mode in async_modes:
            cloned_graph = clone_graph(async_graph)
            cloned_graph.set_graph_mode(stage_mode, execution_mode)

            run_tasks = {tag: list(tasks) for tag, tasks in base_tasks.items()}
            start_time = time.perf_counter()
            cloned_graph.start_graph(run_tasks)
            time_list.append(time.perf_counter() - start_time)

        test_table_list.append(time_list)

    time_table: str = format_table(
        test_table_list,
        stage_modes,
        execution_modes,
        r"stage\execution",
    )
    print(f"Time table:\n{time_table}")
    return {
        "table": time_table,
        "stage_modes": stage_modes,
        "sync_modes": sync_modes,
        "async_modes": async_modes if async_graph else [],
    }
