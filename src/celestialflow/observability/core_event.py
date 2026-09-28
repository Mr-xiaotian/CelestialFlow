# observability/core_event.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

type TaskSource = Literal["external", "upstream"]
"""任务进入节点的来源：``"external"`` 为外部注入，``"upstream"`` 为上游下发。"""


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
