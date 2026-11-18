# benchmark/util_clone.py
from __future__ import annotations

from typing import Any, cast

from ..graph import TaskGraph
from ..node import TaskExecutor
from ..node.util_types import AnyTaskNode
from ..runtime.util_errors import ConfigurationError
from ..runtime.util_event import clone_event_client


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
        "max_queue_size": executor.max_queue_size,
        "max_info": executor.max_info,
        "skip_func": executor.skip_func,
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
    cloned.set_retry_exceptions(*executor.retry_exceptions)
    return cloned


def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    克隆任务图

    该工具仅用于 benchmark 场景，因此只支持由 ``TaskExecutor`` 组成的任务图，
    并直接复用 :func:`clone_executor` 克隆所有节点。克隆会覆盖图中已注册的全部节点，
    因此非连通分量与无源环图也能被完整复制。

    克隆体不携带原图 / 原节点的观察者：``clone_executor`` 会创建全新实例，
    共享带计数器的观察者会导致重复计数。

    :param graph: 要克隆的任务图
    :return: 克隆任务图
    :raises ConfigurationError: 图中包含非 ``TaskExecutor`` 节点时抛出
    """
    ordered_nodes: list[TaskExecutor[Any, Any]] = []
    for node_name in graph.get_nodes():
        node: AnyTaskNode = graph.node_dict[node_name]
        if not isinstance(node, TaskExecutor):
            raise ConfigurationError(
                "clone_graph() only supports graphs composed of TaskExecutor nodes"
            )
        ordered_nodes.append(node)

    # 建立原节点名到克隆节点的映射
    name_map: dict[str, TaskExecutor[Any, Any]] = {}
    for node in ordered_nodes:
        name_map[node.get_name()] = clone_executor(node)

    # 构建新的任务图
    all_cloned_nodes: list[AnyTaskNode] = list(name_map.values())

    cloned_graph: TaskGraph = TaskGraph(name=graph.name, graph_mode=graph.graph_mode)
    cloned_graph.set_nodes(all_cloned_nodes)

    # 重建连接
    for from_name, to_names in graph.order_graph.out_edges.items():
        if not to_names:
            continue
        cloned_from: AnyTaskNode = name_map[from_name]
        cloned_to: list[AnyTaskNode] = [name_map[name] for name in to_names]
        cloned_graph.connect([cloned_from], cloned_to)

    cloned_graph.set_ctree(clone_event_client(graph.ctree_client))

    return cloned_graph
