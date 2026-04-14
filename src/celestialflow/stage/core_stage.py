# stage/core_stage.py
from __future__ import annotations

import time
import warnings
from collections.abc import Callable
from multiprocessing import Queue as MPQueue
from multiprocessing import Value as MPValue

from ..runtime import TaskInQueue, TaskMetrics, TaskOutQueue
from ..runtime.util_errors import ExecutionModeError, PickleError, StageModeError
from ..runtime.util_types import NullPrevStage, StageStatus
from ..utils.util_debug import find_unpickleable
from .core_executor import TaskExecutor


class TaskStage(TaskExecutor):
    _name = "Stage"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.show_progress == True:
            warnings.warn(
                "Progress bar display may be unreliable in 'process' stage mode. "
                "All nodes run in parallel in this mode, and tqdm's process-based "
                "implementation is not specifically optimized for this scenario, "
                "potentially causing visual glitches or incorrect progress indicators.",
                RuntimeWarning,
            )

        self.stage_mode = "serial"  # 默认串行
        self.next_stages: list[TaskStage] = []
        self.prev_stages: list[TaskStage | NullPrevStage] = []
        self._pending_prev_bindings: list[TaskStage] = []

        self.init_status()

    def init_metrics(self) -> None:
        """
        初始化任务指标
        """
        self.metrics = TaskMetrics(
            execution_mode="process",
            max_retries=self.max_retries,
            enable_duplicate_check=self.enable_duplicate_check,
        )

    def init_status(self) -> None:
        """
        初始化 stage 共享状态（跨进程可见）。
        建议在 __init__ 里调用一次。
        """
        if not hasattr(self, "_status"):
            self._status = MPValue("i", int(StageStatus.NOT_STARTED))

    def set_func(self, func: Callable):
        """
        设置执行函数

        :param func: 执行函数
        """
        if find_unpickleable(func):
            raise PickleError(func)
        self.func = func
        self._func_name = func.__name__

    def set_execution_mode(self, execution_mode: str) -> None:
        """
        设置执行模式

        :param execution_mode: 执行模式，在 stage 中可以是 'thread'（线程）, 'serial'（串行）
        """
        valid_modes = ("thread", "serial")
        if execution_mode in valid_modes:
            self.execution_mode = execution_mode
        else:
            raise ExecutionModeError(execution_mode, valid_modes)

    def set_graph_context(
        self,
        next_stages: list[TaskStage] | None = None,
        stage_mode: str | None = None,
        stage_name: str | None = None,
    ) -> None:
        """
        设置链式上下文(仅限组成graph时)

        :param next_stages: 后续节点列表
        :param stage_mode: 当前节点执行模式, 可以是 'serial'（串行）或 'process'（并行）
        :param name: 当前节点名称
        """
        self.set_next_stages(next_stages)
        self.set_stage_mode(stage_mode)
        self.set_stage_name(stage_name)
        self._finalize_prev_bindings()

    def set_next_stages(self, next_stages: list[TaskStage] | None) -> None:
        """
        设置后续节点列表, 并为后续节点添加本节点为前置节点

        :param next_stages: 后续节点列表
        """
        self.next_stages = next_stages or []
        for next_stage in self.next_stages:
            next_stage.add_prev_stages(self)

    def set_stage_mode(self, stage_mode: str | None) -> None:
        """
        设置当前节点在graph中的执行模式, 可以是 'serial'（串行）或 'process'（并行）

        :param stage_mode: 当前节点执行模式
        """
        if stage_mode is None:
            return
        if stage_mode == "process":
            self.stage_mode = "process"
        elif stage_mode == "serial":
            self.stage_mode = "serial"
        else:
            raise StageModeError(stage_mode)

    def add_prev_stages(self, prev_stage: TaskStage | NullPrevStage) -> None:
        """
        添加前置节点

        :param prev_stage: 前置节点
        """
        from .core_stages import TaskRouter, TaskSplitter

        if prev_stage in self.prev_stages:
            return
        self.prev_stages.append(prev_stage)

        if isinstance(prev_stage, NullPrevStage):
            return

        if isinstance(prev_stage, TaskSplitter):
            self.metrics.append_task_counter(prev_stage.split_counter)
        elif isinstance(prev_stage, TaskRouter):
            self._pending_prev_bindings.append(prev_stage)
        else:
            self.metrics.append_task_counter(prev_stage.metrics.success_counter)

    def set_stage_name(self, name: str | None = None) -> None:
        """
        设置当前节点名称

        :param name: 当前节点名称
        """
        self._name = name or f"Stage{id(self)}"

        # name 变了，tag 必须失效
        if hasattr(self, "_tag"):
            delattr(self, "_tag")

    def _finalize_prev_bindings(self) -> None:
        """
        绑定前置节点
        """
        from .core_stages import TaskRouter

        if not self._pending_prev_bindings:
            return

        for prev_stage in self._pending_prev_bindings:
            if isinstance(prev_stage, TaskRouter):
                key = self.get_tag()  # 现在已经稳定了
                prev_stage.route_counters.setdefault(key, MPValue("i", 0))
                self.metrics.append_task_counter(prev_stage.route_counters[key])

        self._pending_prev_bindings.clear()

    def get_stage_mode(self) -> str:
        """
        获取当前节点在graph中的执行模式, 可以是 'serial'（串行）或 'process'（并行）

        :return: 当前节点执行模式
        """
        return self.stage_mode

    def get_summary(self) -> dict:
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

    def mark_running(self) -> None:
        """标记：stage 正在运行。"""
        self.init_status()
        with self._status.get_lock():
            self._status.value = int(StageStatus.RUNNING)

    def mark_stopped(self) -> None:
        """标记：stage 已停止（正常结束时在 finally 里调用）。"""
        self.init_status()
        with self._status.get_lock():
            self._status.value = int(StageStatus.STOPPED)

    def get_status(self) -> StageStatus:
        """读取当前状态（返回 StageStatus 枚举）。"""
        self.init_status()
        # 读取也加锁，避免极端情况下读到中间态（虽然 int 很短，但习惯好）
        with self._status.get_lock():
            return StageStatus(self._status.value)

    def start_stage(
        self,
        input_queues: TaskInQueue,
        output_queues: TaskOutQueue,
        fail_queue: MPQueue,
        log_queue: MPQueue,
    ):
        """
        根据 start_type 的值，选择串行、并行执行任务

        :param input_queues: 输入队列
        :param output_queue: 输出队列
        :param fail_queue: 失败队列
        :param log_queue: 日志队列
        """
        start_time = time.perf_counter()
        self.init_progress()
        self.init_env(input_queues, output_queues, fail_queue, log_queue)
        self.log_sinker.start_stage(
            self.get_tag(), self.stage_mode, self.execution_mode, self.max_workers
        )
        self.mark_running()

        try:
            # 根据模式运行对应的任务处理函数
            if self.execution_mode == "thread":
                self.dispatch.run_with_pool(self.execution_mode)
            elif self.execution_mode == "serial":
                self.dispatch.run_in_serial()
            else:
                raise ExecutionModeError(self.execution_mode)

        finally:
            self.mark_stopped()
            self.release_client()

            self.task_progress.close()
            self.log_sinker.end_stage(
                self.get_tag(),
                self.stage_mode,
                self.execution_mode,
                time.perf_counter() - start_time,
                self.metrics.get_success_count(),
                self.metrics.get_error_count(),
                self.metrics.get_duplicate_count(),
            )
