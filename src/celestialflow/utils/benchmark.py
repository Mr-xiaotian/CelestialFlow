# utils/benchmark.py
from __future__ import annotations

import time
import pprint
from collections.abc import Iterable
from typing import Any

from ..graph import TaskGraph
from ..stage import TaskExecutor
from .format import format_table


def benchmark_executor(
    executor: TaskExecutor,
    task_source: Iterable,
    execution_modes: list[str] | None = None,
):
    task_list = list(task_source)
    execution_modes = execution_modes or ["serial", "thread", "process"]

    results = []
    for mode in execution_modes:
        cloned_executor = executor.clone()
        cloned_executor.set_execution_mode(mode)

        start = time.time()
        cloned_executor.start(task_list)
        results.append([time.time() - start])
    
    table_results = format_table(results, execution_modes, ["Time"])
    print("\n" + table_results)


def benchmark_graph(
    graph: TaskGraph,
    init_tasks_dict: dict[str, Iterable],
    stage_modes: list[str] | None = None,
    execution_modes: list[str] | None = None,
) -> dict[str, Any]:
    stage_modes = stage_modes or ["serial", "process"]
    execution_modes = execution_modes or ["serial", "thread"]

    base_tasks = {tag: list(tasks) for tag, tasks in init_tasks_dict.items()}

    test_table_list = []
    fail_by_error_dict = {}
    fail_by_stage_dict = {}

    for stage_mode in stage_modes:
        time_list = []
        for execution_mode in execution_modes:
            cloned_graph = graph.clone()
            cloned_graph.set_graph_mode(stage_mode, execution_mode)

            run_tasks = {tag: list(tasks) for tag, tasks in base_tasks.items()}
            start_time = time.time()
            cloned_graph.start_graph(run_tasks)
            time_list.append(time.time() - start_time)

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

