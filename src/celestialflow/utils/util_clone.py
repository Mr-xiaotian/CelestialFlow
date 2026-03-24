# utils/util_clone.py
from __future__ import annotations

from collections import deque

from ..graph import TaskGraph
from ..stage import TaskExecutor, TaskStage


def _get_clone_init_kwargs(executor: TaskExecutor) -> dict:
    """
    获取克隆执行器的初始化参数

    :param executor: 要克隆的执行器
    :return: 克隆执行器的初始化参数
    """
    return {
        "func": executor.func,
        "execution_mode": executor.execution_mode,
        "max_workers": executor.max_workers,
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
    克隆执行器

    :param executor: 要克隆的执行器
    :return: 克隆执行器
    """
    cloned = TaskExecutor(**_get_clone_init_kwargs(executor))
    cloned.add_retry_exceptions(*executor.metrics.retry_exceptions)
    return cloned


def clone_stage(stage: TaskStage) -> TaskStage:
    """
    克隆节点

    :param stage: 要克隆的节点
    :return: 克隆节点
    """
    cloned = TaskStage(**_get_clone_init_kwargs(stage))

    cloned.add_retry_exceptions(*stage.metrics.retry_exceptions)
    cloned.set_stage_mode(stage.get_stage_mode())
    cloned.set_stage_name(stage.get_name())
    return cloned


def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    克隆任务图

    :param graph: 要克隆的任务图
    :return: 克隆任务图
    """
    visited = set()
    ordered_stages: list[TaskStage] = []
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
        cloned_next_stages = [
            stage_map[id(next_stage)] for next_stage in stage.next_stages
        ]
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
