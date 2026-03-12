# utils/benchmark.py
from __future__ import annotations

import time
import pprint
from collections.abc import Iterable
from typing import List, Any
from collections import deque

from ..graph import TaskGraph
from ..stage import TaskExecutor, TaskStage
from .format import format_table


def _get_clone_init_kwargs(executor: TaskExecutor) -> dict:
    """
    获取克隆执行器的初始化参数
    """
    return {
        "func": executor.func,
        "execution_mode": executor.execution_mode,
        "worker_limit": executor.worker_limit,
        "max_retries": executor.max_retries,
        "max_info": executor.max_info,
        "unpack_task_args": executor.unpack_task_args,
        "enable_success_cache": executor.enable_success_cache,
        "enable_error_cache": executor.enable_error_cache,
        "enable_duplicate_check": executor.enable_duplicate_check,
        "show_progress": executor.show_progress,
        "progress_desc": executor.progress_desc,
        "log_level": executor.log_level,
    }


def clone_executor(executor: TaskExecutor) -> TaskExecutor:
    """
    克隆当前执行器
    """
    cloned = TaskExecutor(**_get_clone_init_kwargs(executor))
    if hasattr(executor, "metrics") and executor.metrics.retry_exceptions:
        cloned.add_retry_exceptions(*executor.metrics.retry_exceptions)
    return cloned


def clone_stage(stage: TaskStage) -> TaskStage:
    """
    克隆当前节点
    """
    cloned = TaskStage(**_get_clone_init_kwargs(stage))
    
    if hasattr(stage, "metrics") and stage.metrics.retry_exceptions:
        cloned.add_retry_exceptions(*stage.metrics.retry_exceptions)
    if hasattr(stage, "stage_mode"):
        cloned.set_stage_mode(stage.stage_mode)
    cloned.set_stage_name(stage.get_name())
    return cloned


def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    克隆当前任务图
    """
    visited = set()
    ordered_stages: List[TaskStage] = []
    queue = deque(graph.root_stages)
    while queue:
        stage = queue.popleft()
        if id(stage) in visited:
            continue
        visited.add(id(stage))
        ordered_stages.append(stage)
        queue.extend(stage.next_stages)

    stage_map = {id(stage): clone_stage(stage) for stage in ordered_stages}

    for stage in ordered_stages:
        cloned_stage = stage_map[id(stage)]
        cloned_stage.next_stages = []
        cloned_stage.prev_stages = []
        cloned_stage._pending_prev_bindings = []

    for stage in ordered_stages:
        cloned_stage = stage_map[id(stage)]
        cloned_next_stages = [stage_map[id(next_stage)] for next_stage in stage.next_stages]
        cloned_stage.set_next_stages(cloned_next_stages)

    for stage in ordered_stages:
        stage_map[id(stage)]._finalize_prev_bindings()

    cloned_root_stages = [stage_map[id(stage)] for stage in graph.root_stages]
    cloned_graph = TaskGraph(
        root_stages=cloned_root_stages,
        schedule_mode=graph.schedule_mode,
        log_level=graph.log_level,
    )

    if graph._use_ctree:
        cloned_graph.set_ctree(
            use_ctree=True,
            host=graph._ctree_host,
            http_port=graph._CTREE_HTTP_PORT,
            grpc_port=graph._ctree_grpc_port,
        )
    if graph._is_report:
        cloned_graph.set_reporter(
            is_report=True,
            host=graph._report_host,
            port=graph._report_port,
        )

    return cloned_graph


def benchmark_executor(
    executor: TaskExecutor,
    task_source: Iterable,
    execution_modes: list[str] | None = None,
):
    task_list = list(task_source)
    execution_modes = execution_modes or ["serial", "thread", "process"]

    results = []
    for mode in execution_modes:
        cloned_executor = clone_executor(executor)
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
            cloned_graph = clone_graph(graph)
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

