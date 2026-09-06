# stage/core_stage.py
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from ..runtime import TaskInQueue, TaskOutQueue
from ..runtime.util_errors import UnconsumedError
from ..runtime.util_estimators import (
    calc_elapsed,
    calc_remaining,
    format_avg_time,
)
from .core_executor import TaskExecutor


class TaskStage[T, R](TaskExecutor[T, R]):
    """任务阶段节点，继承 TaskExecutor 并增加图结构连接能力。

    注意：
    - ``start()`` / ``start_async()`` 为一次性调用；运行前的 setter（``set_execution_mode`` /
      ``set_retry_exceptions`` / ``set_ctree`` / ``add_observer`` 等）允许重复调用。
    - 一次运行后，队列绑定、计数状态与图内关联关系不保证可被安全重置。如需再次运行相同
      节点，请重新创建新的 TaskStage 并接入新的 TaskGraph。
    """

    # ==== 类级类型注解 ====
    _status: int
    _last_elapsed: float
    _last_pending: int
    start_time: float
    execution_mode: str
    task_queue: TaskInQueue[T]
    result_queue: TaskOutQueue[R]

    # ==== 初始化 ====
    def __init__(
        self,
        name: str,
        func: Callable[[T], R] | Callable[[T], Awaitable[R]],
        **kwargs: Any,
    ) -> None:
        """
        :param name: 节点名称
        :param func: 可调用对象
        :param execution_mode: 执行模式，可选 'serial', 'thread', 'async'，默认 'serial'
        :param max_workers: 同时处理数量，默认根据 CPU 核心数动态调整
        :param max_retries: 任务的最大重试次数, 默认值为 1，表示每个任务最多执行两次（一次正常执行 + 一次重试）
        :param max_queue_size: 任务输入队列的最大容量，默认为 0，表示无限制
        :param max_info: 日志中每条信息的最大长度，默认 50
        :param enable_duplicate_check: 是否启用重复检查，默认 False
        :note:
            ``start()`` / ``start_async()`` 为一次性调用；运行前的 setter 与 observer
            注册允许重复调用。
        """
        super().__init__(
            name,
            func,
            **kwargs,
        )

        self._init_status()

    def _init_status(self) -> None:
        """初始化 stage 状态与快照缓存。"""

        # 上报器可能会在节点真正启动前先采集一次快照。
        self.start_time = 0.0
        self._last_elapsed = 0.0
        self._last_pending = 0

    # ==== 绑定 ====
    def get_binding_counter(self, _downstream_name: str) -> Any:
        """
        返回下游 stage 应绑定的计数器，子类可覆写。

        :param _downstream_name: 下游 stage 的唯一名称
        :return: 计数器实例
        """
        return self.metrics.success_counter

    def prev_binding(self, pending_prev_binding: TaskStage[Any, Any]) -> None:
        """
        绑定前置节点，将每个前驱 stage 的计数器注册到当前 stage 的 task_counter 中

        :param pending_prev_binding: 前置节点
        """
        counter = pending_prev_binding.get_binding_counter(self.get_name())
        self.metrics.append_task_counter(counter)

    # ==== 查询 ====
    def snapshot(self, interval: float) -> dict[str, Any]:
        """
        采集当前 stage 的运行时快照。

        :param interval: 快照采集间隔（秒）
        :return: 包含状态、计数、耗时估算等信息的快照字典
        """
        status = self.metrics.get_status()
        stage_counts = self.get_counts()

        elapsed = calc_elapsed(status, self._last_elapsed, self._last_pending, interval)
        remaining = calc_remaining(
            stage_counts["tasks_processed"],
            stage_counts["tasks_pending"],
            elapsed,
        )
        avg_time_str = format_avg_time(elapsed, stage_counts["tasks_processed"])

        # 更新缓存供下次快照使用
        self._last_elapsed = elapsed
        self._last_pending = int(stage_counts["tasks_pending"] or 0)

        return {
            "name": self.get_name(),
            "class_name": self._get_class_name(),
            "execution_mode": self.execution_mode,
            "max_workers": self.max_workers,
            "status": status,
            "start_time": self.start_time,
            "elapsed_time": elapsed,
            "remaining_time": remaining,
            "task_avg_time": avg_time_str,
            **stage_counts,
        }

    # ==== 任务队列 ====
    def drain_task_queue(self) -> None:
        """清空任务队列，将所有任务移至失败队列。"""
        remaining_sources = self.task_queue.drain()

        # 持久化逻辑
        for source in remaining_sources:
            self.handle_task_fail(source, UnconsumedError())
