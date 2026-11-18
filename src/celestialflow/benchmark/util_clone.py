# benchmark/util_clone.py
from __future__ import annotations

from typing import Any, cast, overload

from ..graph import TaskGraph
from ..node import TaskExecutor, TaskRouter, TaskSplitter
from ..node.util_types import AnyTaskNode
from ..runtime.util_errors import ConfigurationError
from ..runtime.util_event import clone_event_client

type CloneableTaskNode = (
    TaskExecutor[Any, Any] | TaskSplitter[Any, Any] | TaskRouter[Any, Any]
)


def _get_clone_init_kwargs(
    node: CloneableTaskNode,
) -> dict[str, Any]:
    """
    获取克隆节点的初始化参数。

    :param node: 要克隆的节点
    :return: 克隆节点的初始化参数
    """
    return {
        "name": node.get_name(),
        "func": node.func,
        "execution_mode": node.execution_mode,
        "max_workers": node.max_workers,
        "max_retries": node.max_retries,
        "max_queue_size": node.max_queue_size,
        "max_info": node.max_info,
        "skip_func": node.skip_func,
    }


@overload
def clone_node[T, R](
    node: TaskExecutor[T, R],
) -> TaskExecutor[T, R]: ...


@overload
def clone_node[T, RItem](
    node: TaskSplitter[T, RItem],
) -> TaskSplitter[T, RItem]: ...


@overload
def clone_node[T, Y](
    node: TaskRouter[T, Y],
) -> TaskRouter[T, Y]: ...


def clone_node(
    node: CloneableTaskNode,
) -> CloneableTaskNode:
    """
    克隆内置任务节点。

    benchmark 场景仅支持框架内置的 ``TaskExecutor`` / ``TaskSplitter`` /
    ``TaskRouter``。克隆体不会复用原节点的观察者、队列与事件客户端。

    :param node: 要克隆的节点
    :return: 克隆节点
    :raises ConfigurationError: 节点类型不在支持范围内
    """
    kwargs = _get_clone_init_kwargs(node)
    if isinstance(node, TaskExecutor):
        cloned = cast(CloneableTaskNode, TaskExecutor(**kwargs))
    elif isinstance(node, TaskSplitter):
        cloned = cast(CloneableTaskNode, TaskSplitter(**kwargs))
    else:
        cloned = cast(CloneableTaskNode, TaskRouter(**kwargs))

    cloned.set_retry_exceptions(*node.retry_exceptions)
    return cloned


def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    克隆任务图

    该工具仅用于 benchmark 场景，因此只支持由内置节点
    ``TaskExecutor`` / ``TaskSplitter`` / ``TaskRouter`` 组成的任务图，并直接复用
    :func:`clone_node` 克隆所有节点。克隆会覆盖图中已注册的全部节点，因此非连通
    分量与无源环图也能被完整复制。

    克隆体不携带原图 / 原节点的观察者：``clone_node`` 会创建全新实例，共享带
    计数器的观察者会导致重复计数。

    :param graph: 要克隆的任务图
    :return: 克隆任务图
    :raises ConfigurationError: 图中包含不受支持的节点类型时抛出
    """
    ordered_nodes: list[CloneableTaskNode] = []
    for node_name in graph.get_nodes():
        node: AnyTaskNode = graph.node_dict[node_name]
        if not isinstance(node, TaskExecutor | TaskSplitter | TaskRouter):
            raise ConfigurationError(
                "clone_graph() only supports graphs composed of TaskExecutor, "
                "TaskSplitter, and TaskRouter nodes"
            )
        ordered_nodes.append(node)

    # 建立原节点名到克隆节点的映射
    name_map: dict[str, CloneableTaskNode] = {}
    for node in ordered_nodes:
        name_map[node.get_name()] = clone_node(node)

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
