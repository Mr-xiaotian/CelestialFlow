# reporter/core_metrics.py
from __future__ import annotations

import time
from threading import Lock

from ..observer import (
    NodeEndEvent,
    NodeStartEvent,
    Observer,
    TaskFailEvent,
    TaskInputEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
)
from ..runtime.util_types import NodeMetrics, NodeStatus


class MetricsObserver(Observer):
    """图级指标观察者（写模型 + 只读视图）。

    持有任务图中每个节点的计数、状态与运行起始时间，并作为观察者从事件中写入：

    - 图结构事件：``on_node_added`` 建立节点存储格，``on_node_connected`` 预置边级计数；
    - 节点生命周期：``on_node_start`` / ``on_node_end`` 维护节点状态；
    - 任务事件：``on_task_input`` 区分外部注入与上游投递，``on_task_success`` /
      ``on_task_fail`` / ``on_task_skip`` 累加对应计数。

    上游投递会同时写入接收方的上游计数与来源方的下游计数，因此无需在节点间共享
    计数器对象，也无需按节点类型特化统计逻辑。

    读取通过 :class:`~celestialflow.runtime.util_types.MetricsView` 协议暴露，
    返回不可变的 :class:`~celestialflow.runtime.util_types.NodeMetrics` 快照。
    单个实例服务一个运行作用域：整张任务图，或独立运行的单节点。
    """

    def __init__(self) -> None:
        """初始化指标观察者及其节点存储格表。"""
        self._lock = Lock()

        self._status: dict[str, NodeStatus] = {}
        self._start_time: dict[str, float] = {}
        self._external: dict[str, int] = {}
        self._success: dict[str, int] = {}
        self._fail: dict[str, int] = {}
        self._skip: dict[str, int] = {}
        self._upstream: dict[str, dict[str, int]] = {}
        self._downstream: dict[str, dict[str, int]] = {}

    # ==== 内部存储 ====

    def _ensure(self, node: str) -> None:
        """
        按需建立节点存储格（幂等）。调用方需自行持有锁。

        :param node: 节点名称
        """
        self._status.setdefault(node, NodeStatus.NOT_STARTED)
        self._start_time.setdefault(node, 0.0)
        self._external.setdefault(node, 0)
        self._success.setdefault(node, 0)
        self._fail.setdefault(node, 0)
        self._skip.setdefault(node, 0)
        self._upstream.setdefault(node, {})
        self._downstream.setdefault(node, {})

    def _build(self, node: str) -> NodeMetrics:
        """
        基于当前存储构造节点快照。调用方需自行持有锁。

        :param node: 节点名称
        """
        external_input = self._external[node]
        upstream_counts = self._upstream[node]
        upstream_input = sum(upstream_counts.values())
        input_total = external_input + upstream_input

        succeeded = self._success[node]
        failed = self._fail[node]
        skipped = self._skip[node]
        processed = succeeded + failed + skipped

        return NodeMetrics(
            node=node,
            status=self._status[node],
            start_time=self._start_time[node],
            external_input=external_input,
            upstream_input=upstream_input,
            input_total=input_total,
            succeeded=succeeded,
            failed=failed,
            skipped=skipped,
            processed=processed,
            pending=max(0, input_total - processed),
            upstream_counts=dict(upstream_counts),
            downstream_counts=dict(self._downstream[node]),
        )

    # ==== 图结构 ====

    def on_node_added(self, node: str) -> None:
        """
        为加入任务图的节点建立存储格。

        :param node: 加入任务图的节点名称
        """
        with self._lock:
            self._ensure(node)

    def on_node_connected(self, from_node: str, to_node: str) -> None:
        """
        预置一条边两侧的上下游计数槽位（以 0 初始化）。

        :param from_node: 上游节点名称
        :param to_node: 下游节点名称
        """
        with self._lock:
            self._ensure(from_node)
            self._ensure(to_node)
            self._upstream[to_node].setdefault(from_node, 0)
            self._downstream[from_node].setdefault(to_node, 0)

    # ==== 节点生命周期 ====

    def on_node_start(self, event: NodeStartEvent) -> None:
        """
        记录节点开始执行。

        :param event: 节点开始执行事件
        """
        with self._lock:
            self._ensure(event.node)
            self._status[event.node] = NodeStatus.RUNNING
            self._start_time[event.node] = time.time()

    def on_node_end(self, event: NodeEndEvent) -> None:
        """
        记录节点结束执行。

        :param event: 节点结束执行事件
        """
        with self._lock:
            self._ensure(event.node)
            self._status[event.node] = NodeStatus.STOPPED

    # ==== 任务事件 ====

    def on_task_input(self, event: TaskInputEvent) -> None:
        """
        记录任务输入。

        外部注入只增加接收方的外部输入计数；上游投递同时增加接收方的上游计数与
        来源方的下游计数。

        :param event: 任务输入事件
        """
        with self._lock:
            self._ensure(event.node)
            if event.from_node is None:
                self._external[event.node] += 1
                return

            self._ensure(event.from_node)
            self._upstream[event.node][event.from_node] = (
                self._upstream[event.node].get(event.from_node, 0) + 1
            )
            self._downstream[event.from_node][event.node] = (
                self._downstream[event.from_node].get(event.node, 0) + 1
            )

    def on_task_success(self, event: TaskSuccessEvent) -> None:
        """
        记录任务成功。

        :param event: 任务成功事件
        """
        with self._lock:
            self._ensure(event.node)
            self._success[event.node] += 1

    def on_task_fail(self, event: TaskFailEvent) -> None:
        """
        记录任务失败。

        :param event: 任务失败事件
        """
        with self._lock:
            self._ensure(event.node)
            self._fail[event.node] += 1

    def on_task_skip(self, event: TaskSkipEvent) -> None:
        """
        记录任务跳过。

        :param event: 任务跳过事件
        """
        with self._lock:
            self._ensure(event.node)
            self._skip[event.node] += 1

    # ==== 只读视图 ====

    def get_node_metrics(self, node: str) -> NodeMetrics | None:
        """
        获取单个节点的指标快照。

        :param node: 节点名称
        :return: 该节点的指标快照；未登记时返回 ``None``
        """
        with self._lock:
            if node not in self._status:
                return None
            return self._build(node)

    def get_graph_metrics(self) -> dict[str, NodeMetrics]:
        """
        获取整图所有节点的指标快照。

        :return: 节点名称到指标快照的映射
        """
        with self._lock:
            return {node: self._build(node) for node in self._status}
