# stage/core_stage.py
from __future__ import annotations

import time
from collections.abc import Callable
from multiprocessing import Queue as MPQueue
from multiprocessing import Value as MPValue

from ..runtime import TaskInQueue, TaskMetrics, TaskOutQueue
from ..runtime.util_errors import ExecutionModeError, PickleError, StageModeError
from ..runtime.util_types import StageStatus
from ..utils.util_debug import find_unpickleable
from .core_executor import TaskExecutor


class TaskStage(TaskExecutor):
    _name = "Stage"

    # ==== 初始化 ====
    def __init__(
        self,
        func,
        execution_mode="serial",
        max_workers=20,
        max_retries=1,
        max_info=50,
        unpack_task_args=False,
        enable_success_cache=False,
        enable_duplicate_check=True,
        stage_mode="serial",
        stage_name=None,
    ):
        """
        :param func: 可调用对象
        :param execution_mode: 执行模式，可选 'serial', 'thread', 'async'
        :param max_workers: 同时处理数量
        :param max_retries: 任务的最大重试次数, 默认值为 1，表示每个任务最多执行两次（一次正常执行 + 一次重试）
        :param max_info: 日志中每条信息的最大长度
        :param unpack_task_args: 是否将任务参数解包
        :param enable_success_cache: 是否启用成功结果缓存, 将成功结果保存在 success_pairs 中
        :param enable_duplicate_check: 是否启用重复检查
        :param stage_mode: 当前节点在graph中的执行模式, 可以是 'serial'（串行）或 'process'（并行）, 默认 'serial'
        :param stage_name: 当前节点名称, 默认 None（会自动生成）
        """
        super().__init__(
            func,
            execution_mode,
            max_workers,
            max_retries,
            max_info,
            unpack_task_args,
            enable_success_cache,
            enable_duplicate_check,
        )

        self.set_stage_mode(stage_mode)
        self.set_stage_name(stage_name)

        self._init_status()

    def _init_metrics(self) -> None:
        """
        初始化任务指标
        """
        self.metrics = TaskMetrics(
            execution_mode="process",
            max_retries=self.max_retries,
            enable_duplicate_check=self.enable_duplicate_check,
        )

    def _init_status(self) -> None:
        """
        初始化 stage 共享状态（跨进程可见）。
        建议在 __init__ 里调用一次。
        """
        if not hasattr(self, "_status"):
            self._status = MPValue("i", int(StageStatus.NOT_STARTED))

    # ==== 配置 ====
    def set_stage_mode(self, stage_mode: str | None) -> None:
        """
        设置当前节点在graph中的执行模式, 可以是 'serial'（串行）或 'process'（并行）

        :param stage_mode: 当前节点执行模式
        """
        if stage_mode == "process":
            self.stage_mode = "process"
        elif stage_mode == "serial":
            self.stage_mode = "serial"
        else:
            raise StageModeError(stage_mode)

    def set_stage_name(self, name: str | None = None) -> None:
        """
        设置当前节点名称

        :param name: 当前节点名称
        """
        self._name = name or f"Stage{id(self)}"

        # name 变了，tag 必须失效
        if hasattr(self, "_tag"):
            delattr(self, "_tag")

    def _set_func(self, func: Callable):
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

    # ==== 绑定 ====
    def get_binding_counter(self, _downstream_tag: str):
        """
        返回下游 stage 应绑定的计数器，子类可覆写。
        """
        return self.metrics.success_counter

    def prev_bindings(self, pending_prev_bindings: list[TaskStage]) -> None:
        """
        绑定前置节点
        """
        for prev_stage in pending_prev_bindings:
            counter = prev_stage.get_binding_counter(self.get_tag())
            self.metrics.append_task_counter(counter)

    # ==== 查询 ====
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

    # ==== 状态 ====
    def mark_running(self) -> None:
        """标记：stage 正在运行。"""
        self._init_status()
        with self._status.get_lock():
            self._status.value = int(StageStatus.RUNNING)

    def mark_stopped(self) -> None:
        """标记：stage 已停止（正常结束时在 finally 里调用）。"""
        self._init_status()
        with self._status.get_lock():
            self._status.value = int(StageStatus.STOPPED)

    def get_status(self) -> StageStatus:
        """读取当前状态（返回 StageStatus 枚举）。"""
        self._init_status()
        # 读取也加锁，避免极端情况下读到中间态（虽然 int 很短，但习惯好）
        with self._status.get_lock():
            return StageStatus(self._status.value)

    # ==== 启动 ====
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
        self._init_progress()
        self.init_env(input_queues, output_queues, fail_queue, log_queue)
        self.log_inlet.start_stage(
            self.get_tag(), self.stage_mode, self.execution_mode, self.max_workers
        )
        self.mark_running()

        try:
            # 根据模式运行对应的任务处理函数
            if self.execution_mode == "thread":
                self.dispatch.dispatch_thread()
            elif self.execution_mode == "serial":
                self.dispatch.dispatch_serial()
            else:
                raise ExecutionModeError(self.execution_mode)

        finally:
            self.mark_stopped()
            self._release_client()

            self.task_progress.close()
            self.log_inlet.end_stage(
                self.get_tag(),
                self.stage_mode,
                self.execution_mode,
                time.perf_counter() - start_time,
                self.metrics.get_success_count(),
                self.metrics.get_error_count(),
                self.metrics.get_duplicate_count(),
            )
