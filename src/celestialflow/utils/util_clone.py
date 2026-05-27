# utils/util_clone.py
from __future__ import annotations

import inspect
from collections import deque
from typing import Any

from ..graph import TaskGraph
from ..stage import TaskExecutor, TaskStage


def _get_clone_init_kwargs(executor: TaskExecutor) -> dict[str, Any]:
    """
    获取克隆执行器的初始化参数

    :param executor: 要克隆的执行器
    :return: 克隆执行器的初始化参数
    """
    return {
        "name": executor.get_name(),
        "func": executor.func,
        "execution_mode": executor.execution_mode,
        "max_workers": executor.max_workers,
        "max_retries": executor.max_retries,
        "max_info": executor.max_info,
        "unpack_task_args": executor.unpack_task_args,
        "enable_duplicate_check": executor.enable_duplicate_check,
        "log_level": executor.log_level,
    }


def clone_executor(executor: TaskExecutor) -> TaskExecutor:
    """
    克隆执行器

    :param executor: 要克隆的执行器
    :return: 克隆执行器
    """
    cloned: TaskExecutor = TaskExecutor(**_get_clone_init_kwargs(executor))
    cloned.add_retry_exceptions(*executor.metrics.retry_exceptions)
    return cloned


def clone_stage(stage: TaskStage) -> TaskStage:
    """
    克隆节点

    :param stage: 要克隆的节点
    :return: 克隆节点
    """
    kwargs: dict[str, Any] = _get_clone_init_kwargs(stage)
    kwargs["stage_mode"] = stage.get_stage_mode()

    stage_cls = type(stage)
    init_params = set(inspect.signature(stage_cls.__init__).parameters.keys()) - {
        "self"
    }
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in init_params}

    cloned: TaskStage = stage_cls(**filtered_kwargs)

    cloned.add_retry_exceptions(*stage.metrics.retry_exceptions)
    return cloned


def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    克隆任务图

    :param graph: 要克隆的任务图
    :return: 克隆任务图
    """
    # BFS 收集所有 stage（通过 graph.out_edges）
    visited: set[str] = set()
    ordered_stages: list[TaskStage] = []
    queue: deque[TaskStage] = deque(graph.get_source_stages())
    while queue:
        stage: TaskStage = queue.popleft()
        stage_name: str = stage.get_name()
        if stage_name in visited:
            continue
        visited.add(stage_name)
        ordered_stages.append(stage)
        for next_stage_name in graph.out_edges.get(stage_name, []):
            next_stage: TaskStage = graph.stage_dict[next_stage_name]
            queue.append(next_stage)

    # 建立 old_name -> cloned_stage 映射
    name_map: dict[str, TaskStage] = {}
    for stage in ordered_stages:
        name_map[stage.get_name()] = clone_stage(stage)

    # 构建新 graph
    all_cloned_stages: list[TaskStage] = list(name_map.values())

    cloned_graph: TaskGraph = TaskGraph(
        schedule_mode=graph.schedule_mode,
        log_level=graph.log_level,
    )
    cloned_graph.set_stages(all_cloned_stages)

    # 重建连接
    for from_name, to_names in graph.out_edges.items():
        if not to_names:
            continue
        cloned_from: TaskStage = name_map[from_name]
        cloned_to: list[TaskStage] = [name_map[name] for name in to_names]
        cloned_graph.connect([cloned_from], cloned_to)

    if graph.use_ctree:
        cloned_graph.set_ctree(
            use_ctree=True,
            host=graph.ctree_host,
            http_port=graph.ctree_http_port,
            grpc_port=graph.ctree_grpc_port,
        )
    if graph.is_report:
        cloned_graph.set_reporter(
            is_report=True,
            host=graph.report_host,
            port=graph.report_port,
        )

    return cloned_graph
