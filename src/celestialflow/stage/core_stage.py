# stage/core_stage.py
from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from queue import Queue as ThreadQueue
from typing import Any

from ..persistence import FailInlet, LogInlet
from ..runtime import TaskInQueue, TaskOutQueue
from ..runtime.util_errors import ExecutionModeError, GraphManagedError, StageModeError
from ..runtime.util_types import StageStatus
from .core_executor import TaskExecutor


class TaskStage(TaskExecutor):
    """任务阶段节点，继承 TaskExecutor 并增加图结构连接与 stage_mode 控制能力。

    注意：
    - TaskStage 是一次性对象，通常由 TaskGraph 管理并参与一次完整运行。
    - 一次运行后，其队列绑定、计数状态和图内关联关系不保证可被安全重置。
    - 如需再次运行相同节点，请重新创建新的 TaskStage，并重新接入新的 TaskGraph。
    """

    # Class-level type annotations (TaskStage-specific)
    _status: int
    start_time: float
    stage_mode: str
    execution_mode: str
    task_queue: TaskInQueue
    result_queue: TaskOutQueue
    fail_inlet: FailInlet
    log_inlet: LogInlet

    # ==== 初始化 ====
    def __init__(
        self,
        name: str,
        func: Callable[..., Any],
        stage_mode: str = "serial",
        **kwargs: Any,
    ):
        """
        :param name: 节点名称
        :param func: 可调用对象
        :param stage_mode: 当前节点在graph中的执行模式, 可以是 'serial'（串行）或 'thread'（线程）, 默认 'serial'
        :note:
            TaskStage 为一次性对象。完成一次由 TaskGraph 驱动的运行后，不应复用当前
            实例再次参与新的运行流程；如需重复执行，请重新创建实例。
        :param execution_mode: 执行模式，可选 'serial', 'thread', 'async'，默认 'serial'
        :param max_workers: 同时处理数量，默认根据 CPU 核心数动态调整
        :param max_retries: 任务的最大重试次数, 默认值为 1，表示每个任务最多执行两次（一次正常执行 + 一次重试）
        :param max_info: 日志中每条信息的最大长度，默认 50
        :param unpack_task_args: 是否将任务参数解包，默认 False
        :param enable_duplicate_check: 是否启用重复检查，默认 True
        :param log_level: 日志级别，默认 'INFO'
        """
        super().__init__(
            name,
            func,
            **kwargs,
        )

        self.set_stage_mode(stage_mode)

        self._init_status()

    def _init_status(self) -> None:
        """初始化 stage 状态。"""
        if not hasattr(self, "_status"):
            self._status = int(StageStatus.NOT_STARTED)
            
        # Reporter 可能会在 stage 真正启动前先采集一次快照。
        self.start_time = 0.0

    # ==== 配置 ====
    def set_stage_mode(self, stage_mode: str) -> None:
        """
        设置当前节点在graph中的执行模式, 可以是 'serial'（串行）或 'thread'（线程）

        :param stage_mode: 当前节点执行模式
        :raises StageModeError: stage_mode 不是 'serial' 或 'thread'
        """
        if stage_mode == "thread":
            self.stage_mode = "thread"
        elif stage_mode == "serial":
            self.stage_mode = "serial"
        else:
            raise StageModeError(stage_mode)

    def set_inlet(
        self, fail_queue: ThreadQueue[Any], log_queue: ThreadQueue[Any]
    ) -> None:
        """
        初始化收集器

        :param fail_queue: 失败队列
        :param log_queue: 日志队列
        """
        self.fail_queue = fail_queue
        self.fail_inlet = FailInlet(self.fail_queue)

        self.log_queue = log_queue
        self.log_inlet = LogInlet(self.log_queue, self.log_level)

    # ==== 绑定 ====
    def get_binding_counter(self, _downstream_name: str) -> Any:
        """
        返回下游 stage 应绑定的计数器，子类可覆写。

        :param _downstream_name: 下游 stage 的唯一名称
        :return: 计数器实例
        """
        return self.metrics.success_counter

    def prev_bindings(self, pending_prev_bindings: list[TaskStage]) -> None:
        """
        绑定前置节点，将每个前驱 stage 的计数器注册到当前 stage 的 task_counter 中

        :param pending_prev_bindings: 前置节点列表
        """
        for prev_stage in pending_prev_bindings:
            counter = prev_stage.get_binding_counter(self.get_name())
            self.metrics.append_task_counter(counter)

    # ==== 查询 ====
    def get_stage_mode(self) -> str:
        """
        获取当前节点在graph中的执行模式

        :return: 当前节点执行模式
        """
        return self.stage_mode

    def get_summary(self) -> dict[str, Any]:
        """
        获取当前节点的状态快照
            - name / execution_mode 等来自 TaskExecutor（执行实体视角）
            - stage_mode 表示任务图中的逻辑节点语义

        :return: 当前节点状态快照
        包括执行器名称(name)、函数名(func_name)、类型名(class_name)、执行模式(execution_mode)、节点模式(stage_mode)
        """
        return {
            **super().get_summary(),
            "stage_mode": self.get_stage_mode(),
        }

    # ==== 状态 ====
    def mark_running(self) -> None:
        """标记：stage 正在运行。"""
        self._status = int(StageStatus.RUNNING)

    def mark_stopped(self) -> None:
        """标记：stage 已停止（正常结束时在 finally 里调用）。"""
        self._status = int(StageStatus.STOPPED)

    def get_status(self) -> StageStatus:
        """读取当前状态（返回 StageStatus 枚举）。"""
        return StageStatus(self._status)

    # ==== 启动 ====
    def start(self, task_source: Any) -> None:
        raise GraphManagedError(
            f"Stage {self.get_name()} is managed by a TaskGraph. Use TaskGraph.start_graph() instead of calling start() directly."
        )

    def start_stage(self) -> None:
        """
        根据 execution_mode 的值，选择串行、线程或异步执行任务。

        :raises ExecutionModeError: execution_mode 不为合法值时触发
        :note:
            TaskStage 为一次性对象；当前实例完成一次 start_stage() 生命周期后，不保
            证可安全再次运行。需要重复执行时请重新创建 TaskStage。
        """
        self.start_time = time.time()
        _start = time.perf_counter()

        self._init_state()

        self.log_inlet.start_stage(
            self.get_name(), self.stage_mode, self._get_execution_mode_desc()
        )
        self.mark_running()

        try:
            # 根据模式运行对应的任务处理函数
            if self.execution_mode == "thread":
                self.dispatch.dispatch_thread()
            elif self.execution_mode == "serial":
                self.dispatch.dispatch_serial()
            elif self.execution_mode == "async":
                asyncio.run(self.dispatch.dispatch_async())
            else:
                raise ExecutionModeError(self.execution_mode)

        finally:
            self.mark_stopped()

            self._notify("on_finish")
            self.log_inlet.end_stage(
                self.get_name(),
                self.stage_mode,
                self._get_execution_mode_desc(),
                time.perf_counter() - _start,
                self.metrics.get_success_count(),
                self.metrics.get_error_count(),
                self.metrics.get_duplicate_count(),
            )
