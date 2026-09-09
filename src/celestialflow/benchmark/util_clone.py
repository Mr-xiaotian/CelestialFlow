# benchmark/util_clone.py
from __future__ import annotations

from collections import deque
from typing import Any, cast
from urllib.parse import urlparse

from ..graph import TaskGraph
from ..observability import NullTaskReporter, ReporterProtocol, TaskReporter
from ..runtime.util_errors import ConfigurationError
from ..runtime.util_event import clone_event_client
from ..stage import TaskExecutor
from ..stage.util_types import AnyTaskExecutor


def _get_clone_init_kwargs[T, R](
    executor: TaskExecutor[T, R],
) -> dict[str, Any]:
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
        "enable_duplicate_check": executor.enable_duplicate_check,
    }


def clone_executor[T, R](
    executor: TaskExecutor[T, R],
) -> TaskExecutor[T, R]:
    """
    克隆执行器

    :param executor: 要克隆的执行器
    :return: 克隆执行器
    """
    cloned = cast(TaskExecutor[T, R], TaskExecutor(**_get_clone_init_kwargs(executor)))
    cloned.set_retry_exceptions(*executor.metrics.retry_exceptions)
    return cloned


def _clone_reporter(
    reporter: ReporterProtocol,
    task_graph: TaskGraph,
) -> ReporterProtocol:
    """
    克隆 reporter 配置并绑定到新的任务图实例。

    :param reporter: 原任务图绑定的 reporter
    :param task_graph: 新的任务图实例
    :return: 新的 reporter
    :raises ConfigurationError: reporter 类型不支持克隆
    """
    if isinstance(reporter, NullTaskReporter):
        return NullTaskReporter()

    if isinstance(reporter, TaskReporter):
        parsed = urlparse(reporter.base_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 80
        return TaskReporter(host=host, port=port, task_graph=task_graph)

    raise ConfigurationError(
        f"unsupported reporter type for clone_graph(): {type(reporter).__name__}"
    )


def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    克隆任务图

    图中的节点现在统一使用 ``TaskExecutor``，因此这里直接复用
    :func:`clone_executor` 克隆所有节点。

    :param graph: 要克隆的任务图
    :return: 克隆任务图
    """
    # 通过广度优先遍历收集所有节点（沿用任务图有序图的出边顺序）
    visited: set[str] = set()
    ordered_stages: list[AnyTaskExecutor] = []
    queue: deque[AnyTaskExecutor] = deque(
        graph.stage_dict[source_name] for source_name in graph.get_source_stages()
    )
    while queue:
        stage: AnyTaskExecutor = queue.popleft()
        stage_name: str = stage.get_name()
        if stage_name in visited:
            continue
        visited.add(stage_name)
        ordered_stages.append(stage)
        for next_stage_name in graph.order_graph.out_edges.get(stage_name, []):
            next_stage: AnyTaskExecutor = graph.stage_dict[next_stage_name]
            queue.append(next_stage)

    # 建立原节点名到克隆节点的映射
    name_map: dict[str, AnyTaskExecutor] = {}
    for stage in ordered_stages:
        name_map[stage.get_name()] = clone_executor(stage)

    # 构建新的任务图
    all_cloned_stages: list[AnyTaskExecutor] = list(name_map.values())

    cloned_graph: TaskGraph = TaskGraph(name=graph.name, graph_mode=graph.graph_mode)
    cloned_graph.set_stages(all_cloned_stages)

    # 重建连接
    for from_name, to_names in graph.order_graph.out_edges.items():
        if not to_names:
            continue
        cloned_from: AnyTaskExecutor = name_map[from_name]
        cloned_to: list[AnyTaskExecutor] = [name_map[name] for name in to_names]
        cloned_graph.connect([cloned_from], cloned_to)

    cloned_graph.set_ctree(clone_event_client(graph.ctree_client))
    cloned_graph.set_reporter(_clone_reporter(graph.reporter, cloned_graph))

    return cloned_graph
