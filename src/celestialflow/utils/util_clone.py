# utils/util_clone.py
from __future__ import annotations

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
    cloned: TaskStage = TaskStage(**kwargs)

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
    queue: deque[TaskStage] = deque(graph.root_stages)
    while queue:
        stage: TaskStage = queue.popleft()
        tag: str = stage.get_tag()
        if tag in visited:
            continue
        visited.add(tag)
        ordered_stages.append(stage)
        for next_tag in graph.out_edges.get(tag, []):
            next_stage: TaskStage = graph.stage_runtime_dict[next_tag].stage
            queue.append(next_stage)

    # 建立 old_tag -> cloned_stage 映射
    tag_map: dict[str, TaskStage] = {}
    for stage in ordered_stages:
        tag_map[stage.get_tag()] = clone_stage(stage)

    # 构建新 graph
    cloned_root_stages: list[TaskStage] = [tag_map[s.get_tag()] for s in graph.root_stages]
    all_cloned_stages: list[TaskStage] = list(tag_map.values())

    cloned_graph: TaskGraph = TaskGraph(
        schedule_mode=graph.schedule_mode,
        log_level=graph.log_level,
    )
    cloned_graph.set_stages(cloned_root_stages, all_cloned_stages)

    # 重建连接
    for from_tag, to_tags in graph.out_edges.items():
        if not to_tags:
            continue
        cloned_from: TaskStage = tag_map[from_tag]
        cloned_to: list[TaskStage] = [tag_map[t] for t in to_tags]
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
