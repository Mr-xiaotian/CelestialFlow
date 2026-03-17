# utils/benchmark.py
from __future__ import annotations

import time
import pprint
from collections.abc import Iterable
from typing import Any

from ..graph import TaskGraph
from ..stage import TaskExecutor
from .util_clone import clone_executor, clone_graph
from .util_format import format_table


async def benchmark_executor(
    sync_executor: TaskExecutor,
    async_executor: TaskExecutor,
    task_source: Iterable,
    sync_modes: list[str] | None = None,
    async_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对执行器进行基准测试

    :param executor: 要测试的执行器
    :param task_source: 任务源，用于生成任务列表
    :param execution_modes: 要测试的执行模式列表，默认包括 "serial", "thread", "process"
    :return: 包含测试结果的字典
    """
    task_list = list(task_source)
    sync_modes = sync_modes or ["serial", "thread", "process"]
    async_modes = async_modes or ["async"]

    results = []
    for mode in sync_modes:
        cloned_executor = clone_executor(sync_executor)
        cloned_executor.set_execution_mode(mode)

        start = time.perf_counter()
        cloned_executor.start(task_list)
        results.append([time.perf_counter() - start])

    for mode in async_modes:
        cloned_executor = clone_executor(async_executor)
        cloned_executor.set_execution_mode(mode)

        start = time.perf_counter()
        await cloned_executor.start_async(task_list)
        results.append([time.perf_counter() - start])

    table_results = format_table(results, sync_modes + async_modes, ["Time"])
    print("\n" + table_results)


def benchmark_graph(
    graph: TaskGraph,
    init_tasks_dict: dict[str, Iterable],
    stage_modes: list[str] | None = None,
    execution_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对任务图进行基准测试

    :param graph: 要测试的任务图
    :param init_tasks_dict: 初始任务字典，键为任务标签，值为任务列表
    :param stage_modes: 要测试的节点执行模式列表，默认包括 "serial", "process"
    :param execution_modes: 要测试的执行模式列表，默认包括 "serial", "thread"
    :return: 包含测试结果的字典
    """
    stage_modes = stage_modes or ["serial", "process"]
    execution_modes = execution_modes or ["serial", "thread"]

    base_tasks = {tag: list(tasks) for tag, tasks in init_tasks_dict.items()}

    test_table_list = []
    fail_by_error_dict = {}
    fail_by_stage_dict = {}

    for stage_mode in stage_modes:
        time_list = []
        for execution_mode in execution_modes:
            cloned_graph = clone_graph(graph)
            cloned_graph.set_graph_mode(stage_mode, execution_mode)

            run_tasks = {tag: list(tasks) for tag, tasks in base_tasks.items()}
            start_time = time.perf_counter()
            cloned_graph.start_graph(run_tasks)
            time_list.append(time.perf_counter() - start_time)

            fail_by_stage_dict.update(cloned_graph.get_fail_by_stage_dict())
            fail_by_error_dict.update(cloned_graph.get_fail_by_error_dict())

        test_table_list.append(time_list)

    time_table = format_table(
        test_table_list,
        stage_modes,
        execution_modes,
        r"stage\execution",
    )
    print(f"Time table:\n{time_table}")
    print(f"Fail stage dict: \n{pprint.pformat(fail_by_stage_dict)}")
    print(f"Fail error dict: \n{pprint.pformat(fail_by_error_dict)}")
