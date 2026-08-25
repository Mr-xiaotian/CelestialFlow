# stage/core_executor.py
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
from ..runtime.util_errors import ConfigurationError, InvalidOptionError, PersistedError
from ..runtime.util_event import EventClient, LocalEventClient
from ..runtime.util_format import format_repr
from ..runtime.util_types import (
    CTreeEvent,
    TerminationSignal,
)
from .core_dispatch import TaskDispatch
from .util_callable import validate_executor_func_signature


class TaskExecutor[T, R]:
    """任务执行器基类，支持串行、线程和异步三种执行模式。

    注意：
    - TaskExecutor 是一次性对象，设计上只应执行一次完整的 start()/start_async() 生命周期。
    - 执行过程中会创建并持有队列、spout/inlet、统计状态等运行期资源，
      不保证在一次运行结束后可被安全重置并再次复用。
    - 如需重复执行同一逻辑，请重新创建新的 TaskExecutor 实例。
    """

    # ==== 类级类型注解 ====
    task_queue: TaskInQueue[T]
    result_queue: TaskOutQueue[R]
    max_workers: int
    max_retries: int
    max_info: int
    enable_duplicate_check: bool
    metrics: TaskMetrics
    dispatch: TaskDispatch[T, R]
    execution_mode: str
    _name: str
    func: Callable[[T], R] | Callable[[T], Awaitable[R]]
    _func_name: str
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
        初始化 TaskExecutor

        :param name: 节点/管理器名称
        :param func: 可调用对象
        :param execution_mode: 执行模式，可选 'serial', 'thread', 'async'，默认 'serial'
        :param max_workers: 同时处理数量，默认根据 CPU 核心数动态调整
        :param max_retries: 任务的最大重试次数, 默认值为 1，表示每个任务最多执行两次（一次正常执行 + 一次重试）
        :param max_queue_size: 任务输入队列的最大容量，默认为 0，表示无限制
        :param max_info: 日志中每条信息的最大长度，默认 50
        :param enable_duplicate_check: 是否启用重复检查，默认 False
        :note:
            TaskExecutor 为一次性对象。完成一次 start()/start_async() 后，不应复用
            同一实例再次启动；如需重复执行，请重新创建实例。
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

        self.dispatch = TaskDispatch(self, self.func, self.max_workers)
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
                f"TaskExecutor func '{getattr(func, '__name__', type(func).__name__)}' "
                "must accept exactly one positional task argument."
            )

        self.func = func
        self._func_name = func.__name__

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
        设置执行器使用的事件客户端。

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

    def get_full_name(self) -> str:
        """
        获取当前节点/管理器全名

        :return: 当前节点/管理器全名，格式为 "name(execution_mode-max_workers)"
        """
        extra_desc = (
            f"{self.execution_mode}-{self.max_workers}"
            if self.execution_mode != "serial"
            else "serial"
        )
        return f"{self.get_name()}({extra_desc})"

    def get_func_name(self) -> str:
        """
        获取当前节点函数名

        :return: 当前节点函数名
        """
        return self._func_name

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

    def get_summary(self) -> dict[str, Any]:
        """
        获取当前节点的基础摘要信息。

        :return: 当前节点摘要，
            包括执行器名称 ``name``、函数名 ``func_name``、执行模式
            ``execution_mode`` 与 ``max_workers``
        """
        return {
            "name": self.get_name(),
            "func_name": self.get_func_name(),
            "execution_mode": self.execution_mode,
            "max_workers": self.max_workers,
        }

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

    # ==== 任务输入 ====
    def put_task(self, task: T) -> None:
        """
        将单个任务封装为 TaskEnvelope 并放入队列。

        :param task: 原始任务数据
        """
        input_id = self.ctree_client.emit(
            CTreeEvent.TASK_INPUT,
            payload=self.get_summary(),
        )
        envelope: TaskEnvelope[T] = TaskEnvelope(task, input_id)
        self.task_queue.put(envelope)
        self.metrics.add_task_count()

        get_lifecycle_inlet().task_in(self.get_name(), input_id, task)
        get_log_inlet().task_input(
            self.get_func_name(),
            self._get_repr(task),
            self.get_name(),
            input_id,
        )

    def put_signal(self) -> None:
        """
        放入终止信号到队列。
        """
        termination_id = self.ctree_client.emit(
            CTreeEvent.TERMINATION_INPUT,
            payload=self.get_summary(),
        )
        signal = TerminationSignal(termination_id, source="input")
        self.task_queue.put(signal)
        get_log_inlet().termination_input(
            self.get_func_name(),
            self.get_name(),
            termination_id,
        )

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
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        result_id = self.ctree_client.emit(
            CTreeEvent.TASK_SUCCESS,
            parents=[task_id],
            payload=self.get_summary(),
        )

        self.metrics.add_success_count()
        get_lifecycle_inlet().task_success(task_id, result)

        get_log_inlet().task_success(
            self.get_func_name(),
            self._get_repr(task),
            self.execution_mode,
            self._get_repr(result),
            time.perf_counter() - start_time,
            task_id,
            result_id,
        )

        for target_name in self.result_queue.get_target_names():
            downstream_input_id = self.ctree_client.emit(
                CTreeEvent.TASK_INPUT,
                parents=[result_id],
                payload=self.get_summary(),
            )
            get_lifecycle_inlet().task_in(target_name, downstream_input_id, result)
            downstream_envelope: TaskEnvelope[R] = TaskEnvelope(
                task=result,
                id=downstream_input_id,
            )
            self.result_queue.put_target(downstream_envelope, target_name)

    def emit_retry_envelope(
        self,
        task_envelope: TaskEnvelope[T],
        exception: Exception,
        retry_time: int,
    ) -> TaskEnvelope[T]:
        """
        为重试任务生成新的信封 ID 并记录日志

        :param task_envelope: 发生异常的任务
        :param exception: 捕获的异常
        :param retry_time: 当前重试次数
        :return: 重试的任务信封
        """
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        retry_id = self.ctree_client.emit(
            f"{CTreeEvent.TASK_RETRY_PREFIX}{retry_time}",
            parents=[task_id],
            payload=self.get_summary(),
        )

        retry_envelope: TaskEnvelope[T] = TaskEnvelope(
            task=task,
            id=retry_id,
        )

        get_log_inlet().task_retry(
            self.get_func_name(),
            self._get_repr(task),
            retry_time,
            exception,
            task_id,
            retry_id,
        )
        get_lifecycle_inlet().task_retry(task_id, retry_id)

        return retry_envelope

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
            payload=self.get_summary(),
        )

        self.metrics.add_fail_count()

        get_lifecycle_inlet().task_fail(task_id, error_id, exception)
        get_log_inlet().task_fail(
            self.get_func_name(),
            self._get_repr(task),
            exception,
            task_id,
            error_id,
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
            payload=self.get_summary(),
        )
        get_log_inlet().task_duplicate(
            self.get_func_name(),
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
        异步启动任务执行器

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
        从 sqlite 持久化库中读取当前 stage 的任务并启动执行。

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
        self.metrics.on_start(self.get_full_name(), 0)

        get_log_inlet().start_executor(
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
            get_log_inlet().end_executor(
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
            TaskExecutor 为一次性对象；当前实例完成一次 start() 后，不保证可安全再次
            调用 start()。如需再次执行，请创建新的 TaskExecutor。
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
            TaskExecutor 为一次性对象；当前实例完成一次 start_async() 后，不保证可
            安全再次调用。需要重复执行时请创建新的 TaskExecutor。
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
            get_log_inlet().executor_crash(self.get_name(), exception)
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
