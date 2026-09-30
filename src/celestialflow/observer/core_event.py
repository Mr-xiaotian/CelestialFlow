# observer/core_event.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

type TaskSource = Literal["external", "upstream"]
"""任务进入节点的来源：``"external"`` 为外部注入，``"upstream"`` 为上游下发。"""

type ReporterFailureKind = Literal[
    "loop",
    "pull_interval",
    "pull_tasks",
    "push_errors",
    "push_status",
    "push_graph_meta",
    "shutdown",
]
"""上报器诊断失败的类别。"""


@dataclass(frozen=True, slots=True)
class NodeStartEvent:
    """节点启动事件。

    :param node: 节点名称
    :param execution_mode: 节点执行模式
    :param max_workers: 最大并发数
    :param task_count: 启动时刻的任务总数（外部注入与上游提供之和）
    """

    node: str
    execution_mode: str
    max_workers: int
    task_count: int


@dataclass(frozen=True, slots=True)
class NodeEndEvent:
    """节点结束事件。

    :param node: 节点名称
    :param execution_mode: 节点执行模式
    :param max_workers: 最大并发数
    :param elapsed: 节点运行耗时（秒）
    :param succeeded: 成功任务数
    :param failed: 失败任务数
    :param skipped: 跳过任务数
    """

    node: str
    execution_mode: str
    max_workers: int
    elapsed: float
    succeeded: int
    failed: int
    skipped: int


@dataclass(frozen=True, slots=True)
class TaskInputEvent:
    """任务输入事件。

    :param node: 接收任务的节点名称
    :param task: 原始任务数据
    :param task_repr: 任务的可读表示
    :param input_id: 当前输入事件 ID
    :param source: 任务来源
    """

    node: str
    task: Any
    task_repr: str
    input_id: int
    source: TaskSource


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
class WorkerCrashEvent:
    """工作器崩溃事件。

    :param node: 崩溃工作器所属的节点名称
    :param exception: 导致崩溃的异常
    """

    node: str
    exception: Exception


@dataclass(frozen=True, slots=True)
class GraphStartEvent:
    """任务图启动事件。

    :param graph: 任务图名称
    :param graph_mode: 任务图运行模式
    :param structure_list: 任务图结构信息列表
    """

    graph: str
    graph_mode: str
    structure_list: list[str]


@dataclass(frozen=True, slots=True)
class GraphEndEvent:
    """任务图结束事件。

    :param graph: 任务图名称
    :param elapsed: 任务图运行耗时（秒）
    """

    graph: str
    elapsed: float


@dataclass(frozen=True, slots=True)
class InjectSuccessEvent:
    """任务/终止符注入成功事件。

    :param target_node: 注入目标的节点名称
    :param task_datas: 注入的数据
    """

    target_node: str
    task_datas: Any


@dataclass(frozen=True, slots=True)
class InjectFailedEvent:
    """任务/终止符注入失败事件。

    :param target_node: 注入目标的节点名称
    :param task_datas: 注入的数据
    :param exception: 导致注入失败的异常
    """

    target_node: str
    task_datas: Any
    exception: Exception


@dataclass(frozen=True, slots=True)
class ReporterStopEvent:
    """上报器停止事件。"""


@dataclass(frozen=True, slots=True)
class ReporterFailureEvent:
    """上报器诊断失败事件。

    :param kind: 失败的类别
    :param exception: 导致失败的异常
    """

    kind: ReporterFailureKind
    exception: Exception
