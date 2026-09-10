# node/core_node.py
from __future__ import annotations

import inspect
import os
import time
from collections.abc import Awaitable, Callable, Iterable
from pathlib import Path
from typing import Any, cast

from ..observability import BaseObserver
from ..persistence import (
    funnel_scope,
    get_lifecycle_inlet,
    get_lifecycle_spout,
    get_log_inlet,
)
from ..persistence.util_sqlite import load_tasks_grouped_by_stage
from ..runtime import (
    TaskEnvelope,
    TaskInQueue,
    TaskMetrics,
    TaskOutQueue,
)
from ..runtime.util_errors import (
    ConfigurationError,
    InvalidOptionError,
    PersistedError,
    UnconsumedError,
)
from ..runtime.util_estimators import (
    calc_elapsed,
    calc_remaining,
    format_avg_time,
)
from ..runtime.util_event import EventClient, LocalEventClient
from ..runtime.util_format import format_repr
from ..runtime.util_types import (
    CTreeEvent,
    TerminationSignal,
    ValueWrapper,
)
from .core_dispatch import TaskDispatch
from .util_callable import validate_executor_func_signature


class BaseTaskNode[T, R]:
    """任务节点基类，支持串行、线程和异步三种执行模式。

    注意：
    - ``start()`` / ``start_async()`` 为一次性调用；启动并运行完成后，不保证当前实例可被
      安全重置并再次复用。如需重复执行同一逻辑，请重新创建新的 BaseTaskNode 实例。
    - 启动前的 setter（``set_execution_mode`` / ``set_retry_exceptions`` / ``set_ctree`` /
      ``add_observer`` 等）允许在 start 之前多次调用。
    - 任务输入/结果队列、metrics 状态与 ctree 客户端由节点自身持有；全局
      ``LifecycleSpout`` / ``LogSpout`` 由 :func:`funnel_scope` 负责启停，BaseTaskNode
      自身不直接持有 spout/inlet 实例。
    """

    # ==== 类级类型注解 ====
    _name: str
    _last_elapsed: float
    _last_pending: int
    task_queue: TaskInQueue[T]
    result_queue: TaskOutQueue[R]
    max_workers: int
    max_retries: int
    max_info: int
    enable_duplicate_check: bool
    metrics: TaskMetrics
    dispatch: TaskDispatch[T, R]
    execution_mode: str
    func: Callable[[T], R] | Callable[[T], Awaitable[R]]
    ctree_client: EventClient

    # ==== 初始化 ====
    def __init__(
        self,
        name: str,
        func: Callable[[T], R] | Callable[[T], Awaitable[R]],
        *,
        execution_mode: str = "serial",
        max_workers: int | None = None,
        max_retries: int = 1,
        max_queue_size: int = 0,
        max_info: int = 50,
        enable_duplicate_check: bool = False,
    ):
        """
        初始化 BaseTaskNode

        :param name: 节点/管理器名称
        :param func: 可调用对象
        :param execution_mode: 执行模式，可选 'serial', 'thread', 'async'，默认 'serial'
        :param max_workers: 同时处理数量，默认根据 CPU 核心数动态调整
        :param max_retries: 任务的最大重试次数, 默认值为 1，表示每个任务最多执行两次（一次正常执行 + 一次重试）
        :param max_queue_size: 任务输入队列的最大容量，默认为 0，表示无限制
        :param max_info: 日志中每条信息的最大长度，默认 50
        :param enable_duplicate_check: 是否启用重复检查，默认 False
        :note:
            ``start()`` / ``start_async()`` 为一次性调用；启动前的 setter 与 observer
            注册允许重复调用。
        """

        self.set_name(name)
        self._set_func(func)

        self.set_execution_mode(execution_mode)
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.max_retries = max_retries
        self.max_queue_size = max_queue_size
        self.max_info = max_info
        self.enable_duplicate_check = enable_duplicate_check

        self.set_ctree(LocalEventClient())

        # IDE 类型检查器会把这里的 ``self`` 视为更宽的 ``Self``，
        # 显式收窄为 ``BaseTaskNode[T, R]`` 可避免初始化阶段的误报。
        self.dispatch = TaskDispatch(
            cast(BaseTaskNode[T, R], self), self.func, self.max_workers
        )
        self.task_queue = TaskInQueue(
            out_name=self.get_name(),
            maxsize=self.max_queue_size,
        )
        self.result_queue = TaskOutQueue(
            in_name=self.get_name(),
        )
        self.metrics = TaskMetrics(
            enable_duplicate_check=self.enable_duplicate_check,
        )

        # 上报器可能会在节点真正启动前先采集一次快照。
        self.start_time = 0.0
        self._last_elapsed = 0.0
        self._last_pending = 0

    # ==== 观察者 ====
    def add_observer(self, observer: BaseObserver) -> None:
        """
        注册观察者。

        :param observer: 要注册的观察者实例
        """
        self.metrics.add_observer(observer)

    def remove_observer(self, observer: BaseObserver) -> None:
        """
        移除观察者。

        :param observer: 要移除的观察者实例
        """
        self.metrics.remove_observer(observer)

    # ==== 配置 ====

    def _set_func(
        self,
        func: Callable[[T], R] | Callable[[T], Awaitable[R]],
    ) -> None:
        """
        设置执行函数

        :param func: 执行函数
        """
        parameter_count = validate_executor_func_signature(func)
        if parameter_count != 1:
            raise ConfigurationError(
                f"BaseTaskNode func '{getattr(func, '__name__', type(func).__name__)}' "
                "must accept exactly one positional task argument."
            )

        self.func = func

    def set_execution_mode(self, execution_mode: str) -> None:
        """
        设置执行模式

        :param execution_mode: 执行模式，可以是 'thread'（线程）, 'async'（异步）, 'serial'（串行）
        :raises InvalidOptionError: execution_mode 不是合法值
        :raises ConfigurationError: 异步模式下 func 不是协程函数
        """
        valid_modes = ("serial", "thread", "async")
        if execution_mode not in valid_modes:
            raise InvalidOptionError("execution mode", execution_mode, valid_modes)
        self.execution_mode = execution_mode

        if execution_mode == "async" and not inspect.iscoroutinefunction(self.func):
            raise ConfigurationError(
                f"execution_mode is 'async' but '{self.func.__name__}' is not a coroutine function"
            )

    def set_ctree(self, ctree_client: EventClient) -> None:
        """
        设置节点使用的事件客户端。

        :param ctree_client: 事件客户端实例
        """
        self.ctree_client = ctree_client

    def set_name(self, name: str) -> None:
        """
        设置节点/管理器名称。

        :param name: 节点/管理器名称
        """
        self._name = name

    def set_retry_exceptions(self, *exceptions: type[Exception]) -> None:
        """
        添加需要重试的异常类型

        :param exceptions: 异常类型
        """
        self.metrics.set_retry_exceptions(*exceptions)

    # ==== 查询 ====
    def get_name(self) -> str:
        """
        获取当前节点/管理器名称

        :return: 当前节点/管理器名称
        """
        return self._name

    def _get_class_name(self) -> str:
        """
        获取当前节点类名

        :return: 当前节点类名
        """
        return self.__class__.__name__

    def _get_execution_mode_desc(self) -> str:
        """
        获取当前节点执行模式

        :return: 当前节点执行模式
        """
        return (
            self.execution_mode
            if self.execution_mode == "serial"
            else f"{self.execution_mode}-{self.max_workers}"
        )

    def get_counts(self) -> dict[str, Any]:
        """
        获取当前节点的计数器

        :return: 当前节点计数器
        包括 tasks_input, tasks_succeeded, tasks_failed, tasks_duplicated, tasks_processed, tasks_pending
        """
        return self.metrics.get_counts()

    def get_lifecycle_path(self) -> Path:
        """
        获取任务生命周期持久化路径。

        :return: 生命周期持久化文件的绝对路径，未设置时返回空 Path
        """
        db_path = get_lifecycle_spout().db_path
        if db_path is None:
            return Path()
        return Path(db_path).resolve()

    def snapshot(self, interval: float) -> dict[str, Any]:
        """
        采集当前节点的运行时快照。

        :param interval: 快照采集间隔（秒）
        :return: 包含状态、计数、耗时估算等信息的快照字典
        """
        status = self.metrics.get_status()
        node_counts = self.get_counts()

        elapsed = calc_elapsed(status, self._last_elapsed, self._last_pending, interval)
        remaining = calc_remaining(
            node_counts["tasks_processed"],
            node_counts["tasks_pending"],
            elapsed,
        )
        avg_time_str = format_avg_time(elapsed, node_counts["tasks_processed"])

        # 更新缓存供下次快照使用
        self._last_elapsed = elapsed
        self._last_pending = int(node_counts["tasks_pending"] or 0)

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
            **node_counts,
        }

    # ==== 绑定 ====
    def get_binding_counter(self, _downstream_name: str) -> ValueWrapper:
        """
        返回下游节点应绑定的计数器，子类可覆写。

        :param _downstream_name: 下游节点的唯一名称
        :return: 计数器实例
        """
        raise NotImplementedError

    def prev_binding(self, pending_prev_binding: BaseTaskNode[Any, Any]) -> None:
        """
        绑定前置节点，将每个前驱节点的计数器注册到当前节点的 task_counter 中。

        :param pending_prev_binding: 前置节点
        """
        counter = pending_prev_binding.get_binding_counter(self.get_name())
        self.metrics.append_task_counter(counter)

    # ==== 任务队列 ====
    def put_task(self, task: T) -> None:
        """
        将单个任务封装为 TaskEnvelope 并放入队列。

        :param task: 原始任务数据
        """
        input_id = self.ctree_client.emit(
            CTreeEvent.TASK_INPUT,
        )
        envelope: TaskEnvelope[T] = TaskEnvelope(task, input_id)
        self.task_queue.put(envelope)
        self.metrics.add_task_count()

        get_lifecycle_inlet().task_input(self.get_name(), input_id, task)
        get_log_inlet().task_input(
            self.get_name(),
            self._get_repr(task),
            input_id,
        )

    def put_signal(self) -> None:
        """
        放入终止信号到队列。
        """
        termination_id = self.ctree_client.emit(
            CTreeEvent.TERMINATION_INPUT,
        )
        signal = TerminationSignal(termination_id, source="input")
        self.task_queue.put(signal)
        get_log_inlet().termination_input(
            self.get_name(),
            termination_id,
        )

    def drain_task_queue(self) -> None:
        """清空任务队列，将所有任务移至失败队列。"""
        remaining_sources = self.task_queue.drain()

        # 持久化逻辑
        for source in remaining_sources:
            self.handle_task_fail(source, UnconsumedError())

    def _get_repr(self, task: T | R) -> str:
        """
        获取任务/结果对象的可读字符串表示

        :param task: 任务对象
        :return: 任务信息字符串
        """
        return f"({format_repr(task, self.max_info)})"

    # ==== 结果处理 ====

    def process_task_success(
        self, task_envelope: TaskEnvelope[T], result: R, start_time: float
    ) -> None:
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        raise NotImplementedError

    def handle_task_fail(
        self,
        task_envelope: TaskEnvelope[T],
        exception: Exception,
    ) -> None:
        """
        记录失败任务并持久化错误信息。

        :param task_envelope: 失败的任务
        :param exception: 捕获的异常
        """
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        error_id = self.ctree_client.emit(
            CTreeEvent.TASK_ERROR,
            parents=[task_id],
        )

        self.metrics.add_fail_count()

        get_lifecycle_inlet().task_fail(task_id, error_id, exception)
        get_log_inlet().task_fail(
            self.get_name(),
            self._get_repr(task),
            exception,
            task_id,
            error_id,
        )

    def log_task_retry(
        self,
        task_envelope: TaskEnvelope[T],
        exception: Exception,
        fail_times: int,
    ):
        """
        为重试任务生成新的信封 ID 并记录日志

        :param task_envelope: 发生异常的任务
        :param exception: 捕获的异常
        :param fail_times: 当前失败次数
        """
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        get_log_inlet().task_retry(
            self.get_name(),
            self._get_repr(task),
            fail_times,
            exception,
            task_id,
        )

    def deal_duplicate(self, task_envelope: TaskEnvelope[T]) -> None:
        """
        处理重复任务

        :param task_envelope: 重复的任务
        """
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        self.metrics.add_duplicate_count()
        get_lifecycle_inlet().task_duplicate(task_id)
        duplicate_id = self.ctree_client.emit(
            CTreeEvent.TASK_DUPLICATE,
            parents=[task_id],
        )
        get_log_inlet().task_duplicate(
            self.get_name(),
            self._get_repr(task),
            task_id,
            duplicate_id,
        )

    # ==== 执行 ====

    def run(
        self,
        task_source: Iterable[T],
        *,
        if_put_signal: bool = True,
    ) -> None:
        """
        执行任务

        :param task_source: 任务源
        :param if_put_signal: 是否注入终止信号，默认 True
        :return: ``None``
        """
        with funnel_scope():
            for task in task_source:
                self.put_task(task)
            if if_put_signal:
                self.put_signal()
            self.start()

    async def run_async(
        self,
        task_source: Iterable[T],
        *,
        if_put_signal: bool = True,
    ) -> None:
        """
        异步启动任务节点

        :param task_source: 任务源
        :param if_put_signal: 是否注入终止信号，默认 True
        :return: ``None``
        """
        with funnel_scope():
            for task in task_source:
                self.put_task(task)
            if if_put_signal:
                self.put_signal()
            await self.start_async()

    def restore_db(
        self,
        db_path: str | Path,
        statuses: Iterable[str] | None = None,
        *,
        filter_by_error_type: bool = False,
    ) -> None:
        """
        从 sqlite 持久化库中读取当前节点的任务并启动执行。

        :param db_path: sqlite 数据库文件路径
        :param statuses: 记录状态过滤列表，默认 ``["failed", "pending"]``
        :param filter_by_error_type: 是否按当前执行器的 ``retry_exceptions`` 过滤
            ``error_type``，默认 ``False``
        """
        statuses = ["failed", "pending"] if statuses is None else statuses
        grouped_tasks = load_tasks_grouped_by_stage(db_path, statuses)
        records = grouped_tasks.get(self.get_name(), [])
        tasks: Iterable[T] = []

        if filter_by_error_type:
            retry_error_type_names = self.metrics.get_retry_error_type_names()
            records = [
                record
                for record in records
                if str(record["error_type"]) in retry_error_type_names
                or record["status"] == "pending"
            ]
        tasks = [cast(T, record["task_json"]) for record in records]

        self.run(tasks)

    # ==== 启动 ====

    def _prepare_start(self) -> None:
        """
        启动前准备：重置运行期状态并记录启动日志。

        :return: ``None``
        """
        self.metrics.reset_state()
        self.metrics.on_start(
            f"{self.get_name()}({self._get_execution_mode_desc()})", 0
        )

        get_log_inlet().node_start(
            self.get_name(),
            self.metrics.get_task_count(),
            self._get_execution_mode_desc(),
        )

    def _finish_start(self, start_perf: float) -> list[Exception]:
        """
        启动后清理：记录结束日志并广播执行结束事件。

        :param start_perf: 启动时的时间戳
        """
        error_list: list[Exception] = []

        try:
            get_log_inlet().node_end(
                self.get_name(),
                self._get_execution_mode_desc(),
                time.perf_counter() - start_perf,
                self.metrics.get_success_count(),
                self.metrics.get_fail_count(),
                self.metrics.get_duplicate_count(),
            )
        except Exception as exception:
            error_list.append(exception)

        try:
            self.metrics.on_finish()
        except Exception as exception:
            error_list.append(exception)

        return error_list

    def start(self) -> None:
        """
        根据 execution_mode 的值，选择串行或线程方式执行任务。

        async 模式不支持通过本方法启动，请使用 :meth:`start_async`。

        :raises InvalidOptionError: execution_mode 不是 'serial' 或 'thread' 时触发
        :note:
            ``start()`` 为一次性调用；启动前的 setter 与 observer 注册允许重复调用。
        """
        start_perf = time.perf_counter()
        self.start_time = time.time()
        error_list: list[Exception] = []

        try:
            self._prepare_start()

            if self.execution_mode == "thread":
                self.dispatch.dispatch_thread()
            elif self.execution_mode == "serial":
                self.dispatch.dispatch_serial()
            else:
                raise InvalidOptionError(
                    "execution mode", self.execution_mode, ("serial", "thread")
                )
        except Exception as exception:
            error_list.append(exception)
        finally:
            error_list.extend(self._finish_start(start_perf))

        if error_list:
            raise ExceptionGroup("Errors occurred during execution", error_list)

    async def start_async(self) -> None:
        """
        异步地执行任务。

        :raises InvalidOptionError: execution_mode 不是 'async' 时触发
        :note:
            ``start_async()`` 为一次性调用；启动前的 setter 与 observer 注册允许重复调用。
        """
        if self.execution_mode != "async":
            raise InvalidOptionError("execution mode", self.execution_mode, ("async",))

        start_perf = time.perf_counter()
        self.start_time = time.time()
        error_list: list[Exception] = []

        try:
            self._prepare_start()
            await self.dispatch.dispatch_async()
        except Exception as exception:
            get_log_inlet().node_crash(self.get_name(), exception)
            error_list.append(exception)
        finally:
            error_list.extend(self._finish_start(start_perf))

        if error_list:
            raise ExceptionGroup("Errors occurred during execution", error_list)

    # ==== 结果获取 ====

    def get_success_pairs(self) -> list[tuple[T, R]]:
        """
        获取成功任务的列表

        :return: (task, result) 元组列表
        """
        return get_lifecycle_spout().get_task_result_pairs(self.get_name())

    def get_error_pairs(self) -> list[tuple[T, PersistedError]]:
        """
        获取出错任务的列表

        :return: (task, PersistedError) 元组列表
        """
        task_error_pairs = get_lifecycle_spout().get_task_error_pairs(self.get_name())
        return [
            (task, PersistedError(error_type, error_message))
            for task, (error_type, error_message) in task_error_pairs
        ]
