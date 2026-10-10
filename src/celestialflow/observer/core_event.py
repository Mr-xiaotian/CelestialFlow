# observer/core_event.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class NodeStartEvent:
    """节点启动事件。

    :param node: 节点名称
    :param execution_mode: 节点执行模式
    :param max_workers: 最大并发数
    """

    node: str
    execution_mode: str
    max_workers: int


@dataclass(frozen=True, slots=True)
class NodeEndEvent:
    """节点结束事件。

    :param node: 节点名称
    :param execution_mode: 节点执行模式
    :param max_workers: 最大并发数
    :param elapsed: 节点运行耗时（秒）
    """

    node: str
    execution_mode: str
    max_workers: int
    elapsed: float


@dataclass(frozen=True, slots=True)
class TaskInputEvent:
    """任务输入事件。

    :param node: 接收任务的节点名称
    :param task: 原始任务数据
    :param task_repr: 任务的可读表示
    :param input_id: 当前输入事件 ID
    :param from_node: 上游来源节点名称；``None`` 表示由外部直接注入
    """

    node: str
    task: Any
    task_repr: str
    input_id: int
    from_node: str | None = None


@dataclass(frozen=True, slots=True)
class TaskSuccessEvent:
    """任务成功事件。

    :param node: 节点名称
    :param task: 原始任务数据
    :param task_repr: 任务的可读表示
    :param result: 任务执行结果
    :param result_repr: 结果的可读表示
    :param elapsed: 任务执行耗时（秒）
    :param task_id: 任务输入事件 ID
    :param success_id: 成功事件 ID
    """

    node: str
    task: Any
    task_repr: str
    result: Any
    result_repr: str
    elapsed: float
    task_id: int
    success_id: int


@dataclass(frozen=True, slots=True)
class TaskFailEvent:
    """任务失败事件。

    :param node: 节点名称
    :param task: 原始任务数据
    :param task_repr: 任务的可读表示
    :param exception: 导致失败的异常
    :param task_id: 任务输入事件 ID
    :param error_id: 错误事件 ID
    """

    node: str
    task: Any
    task_repr: str
    exception: Exception
    task_id: int
    error_id: int


@dataclass(frozen=True, slots=True)
class TaskSkipEvent:
    """任务跳过事件。

    :param node: 节点名称
    :param task: 原始任务数据
    :param task_repr: 任务的可读表示
    :param task_id: 任务输入事件 ID
    :param skip_id: 跳过事件 ID
    """

    node: str
    task: Any
    task_repr: str
    task_id: int
    skip_id: int


@dataclass(frozen=True, slots=True)
class TaskRetryEvent:
    """任务重试事件。

    :param node: 节点名称
    :param task: 原始任务数据
    :param task_repr: 任务的可读表示
    :param exception: 导致重试的异常
    :param task_id: 任务输入事件 ID
    :param retry_times: 已重试次数
    """

    node: str
    task: Any
    task_repr: str
    exception: Exception
    task_id: int
    retry_times: int


@dataclass(frozen=True, slots=True)
class TerminationInputEvent:
    """终止信号输入事件。

    :param node: 接收终止信号的节点名称
    :param termination_id: 终止信号事件 ID
    """

    node: str
    termination_id: int


@dataclass(frozen=True, slots=True)
class TerminationMergeEvent:
    """终止信号合并事件。

    :param node: 执行合并的节点名称
    :param parent_ids: 参与合并的终止信号事件 ID 列表
    :param termination_id: 合并后的终止信号事件 ID
    """

    node: str
    parent_ids: list[int]
    termination_id: int


@dataclass(frozen=True, slots=True)
class GraphStartEvent:
    """任务图启动事件。

    :param graph: 任务图名称
    :param graph_mode: 任务图运行模式
    :param start_time: 任务图启动时间
    :param class_name: 任务图类名
    :param is_dag: 是否为 DAG 任务图
    :param nodes: 任务图节点名称列表
    :param edges: 任务图边邻接表
    :param source_nodes: 源节点名称列表
    :param node_meta: 各节点的构建期元信息
    """

    graph: str
    graph_mode: str
    start_time: float
    class_name: str
    is_dag: bool
    nodes: list[str]
    edges: dict[str, list[str]]
    source_nodes: list[str]
    node_meta: dict[str, dict[str, Any]]


@dataclass(frozen=True, slots=True)
class GraphEndEvent:
    """任务图结束事件。

    :param graph: 任务图名称
    :param elapsed: 任务图运行耗时（秒）
    """

    graph: str
    elapsed: float
