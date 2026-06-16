# stage/core_executor.py
from __future__ import annotations

import asyncio
import inspect
import os
import time
import warnings
from collections.abc import Awaitable, Callable, Iterable
from pathlib import Path
from queue import Queue as ThreadQueue
from typing import Any, cast

from celestialtree import Client as CelestialTreeClient
from celestialtree import NullClient as NullCelestialTreeClient

from ..observability import BaseObserver
from ..persistence import (
    FallbackInlet,
    FallbackSpout,
    LogInlet,
    LogSpout,
)
from ..persistence.util_sqlite import load_records_grouped_by_stage
from ..runtime import (
    TaskDispatch,
    TaskEnvelope,
    TaskInQueue,
    TaskMetrics,
    TaskOutQueue,
)
from ..runtime.util_errors import ConfigurationError, ExecutionModeError, PersistedError
from ..runtime.util_types import (
    CTreeEvent,
    TerminationSignal,
)
from ..utils.util_format import format_repr


class TaskExecutor[T, R]:
    """任务执行器基类，支持串行、线程和异步三种执行模式。

    注意：
    - TaskExecutor 是一次性对象，设计上只应执行一次完整的 start()/start_async() 生命周期。
    - 执行过程中会创建并持有队列、spout/inlet、统计状态等运行期资源，
      不保证在一次运行结束后可被安全重置并再次复用。
    - 如需重复执行同一逻辑，请重新创建新的 TaskExecutor 实例。
    """

    # Class-level type annotations
    task_queue: TaskInQueue[T]
    result_queue: TaskOutQueue[R]
    max_workers: int
    max_retries: int
    max_info: int
    enable_duplicate_check: bool
    metrics: TaskMetrics
    dispatch: TaskDispatch[T, R]
    fallback_spout: FallbackSpout
    log_spout: LogSpout
    fallback_inlet: FallbackInlet
    log_inlet: LogInlet
    execution_mode: str
    _name: str
    _func_name: str
    log_level: str
    cree_client: CelestialTreeClient | NullCelestialTreeClient

    # ==== 初始化 ====
    def __init__(
        self,
        name: str,
        func: Callable[[T], R] | Callable[[T], Awaitable[R]],
        *,
        execution_mode: str = "serial",
        max_workers: int | None = None,
        max_retries: int = 1,
        max_info: int = 50,
        enable_duplicate_check: bool = True,
        persist_result: bool = False,
        log_level: str = "INFO",
    ):
        """
        初始化 TaskExecutor

        :param name: 节点/管理器名称
        :param func: 可调用对象
        :param execution_mode: 执行模式，可选 'serial', 'thread', 'async'，默认 'serial'
        :param max_workers: 同时处理数量，默认根据 CPU 核心数动态调整
        :param max_retries: 任务的最大重试次数, 默认值为 1，表示每个任务最多执行两次（一次正常执行 + 一次重试）
        :param max_info: 日志中每条信息的最大长度，默认 50
        :param enable_duplicate_check: 是否启用重复检查，默认 True
        :param persist_result: 是否持久化任务结果，默认 False
        :param log_level: 日志级别，默认 'INFO'
        :note:
            TaskExecutor 为一次性对象。完成一次 start()/start_async() 后，不应复用
            同一实例再次启动；如需重复执行，请重新创建实例。
        """

        self.set_name(name)
        self._set_func(func)

        self.set_execution_mode(execution_mode)
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.max_retries = max_retries
        self.max_info = max_info
        self.enable_duplicate_check = enable_duplicate_check
        self.persist_result = persist_result
        self.set_log_level(log_level)

        self._observers: list[BaseObserver] = []
        self.ctree_client = NullCelestialTreeClient()

        self._init_dispatch()
        self._init_queue()
        self._init_metrics()

    def _init_metrics(self) -> None:
        """
        初始化任务指标
        """
        self.metrics = TaskMetrics(
            enable_duplicate_check=self.enable_duplicate_check,
        )

    def _init_dispatch(self) -> None:
        """
        初始化任务运行器
        """
        self.dispatch = TaskDispatch(self, self.func, self.max_workers)

    def _init_queue(self) -> None:
        """
        初始化输入输出队列
        """
        self.task_queue = TaskInQueue(
            queue=ThreadQueue(),
            source_names=[],
            out_name=self.get_name(),
        )
        self.result_queue = TaskOutQueue(
            queue_list=[],
            target_names=[],
            in_name=self.get_name(),
        )

    def init_env(
        self,
    ) -> None:
        """
        初始化环境
        """
        self._init_state()
        self._init_spout()
        self._init_inlet()

    def _init_state(self) -> None:
        """
        初始化任务状态
        """
        self.metrics.reset_state()

    def _init_spout(self) -> None:
        """
        初始化监听器
        """
        self.fallback_spout = FallbackSpout("executor_fallbacks")
        self.log_spout = LogSpout()

        self.fallback_spout.start()
        self.log_spout.start()

    def _init_inlet(
        self,
    ) -> None:
        """
        初始化收集器
        """
        fallback_queue = self.fallback_spout.get_queue()
        self.fallback_inlet = FallbackInlet(fallback_queue)

        log_queue = self.log_spout.get_queue()
        self.log_inlet = LogInlet(log_queue, self.log_level)

    # ==== Observer ====
    def add_observer(self, observer: BaseObserver) -> None:
        """
        注册观察者。

        :param observer: 要注册的观察者实例
        """
        self._observers.append(observer)

    def remove_observer(self, observer: BaseObserver) -> None:
        """
        移除观察者。

        :param observer: 要移除的观察者实例
        """
        self._observers.remove(observer)

    def _notify(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        """
        通知所有已注册的观察者调用指定方法。

        :param method_name: 要调用的观察者方法名
        :param args: 传递给观察者方法的位置参数
        :param kwargs: 传递给观察者方法的关键字参数
        """
        for observer in self._observers:
            getattr(observer, method_name)(*args, **kwargs)

    # ==== 配置 ====
    def _set_func(
        self,
        func: Callable[[T], R] | Callable[[T], Awaitable[R]],
    ) -> None:
        """
        设置执行函数

        :param func: 执行函数
        """
        try:
            signature = inspect.signature(func)
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(
                f"failed to inspect executor func '{getattr(func, '__name__', type(func).__name__)}'"
            ) from exc

        parameters = list(signature.parameters.values())
        valid_kinds = (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        if len(parameters) != 1 or parameters[0].kind not in valid_kinds:
            raise ConfigurationError(
                
                    f"TaskExecutor func '{getattr(func, '__name__', type(func).__name__)}' "
                    "must accept exactly one positional task argument."
                
            )

        self.func: Callable[[T], R] | Callable[[T], Awaitable[R]] = func
        self._func_name = func.__name__

    def set_execution_mode(self, execution_mode: str) -> None:
        """
        设置执行模式

        :param execution_mode: 执行模式，可以是 'thread'（线程）, 'async'（异步）, 'serial'（串行）
        :raises ExecutionModeError: execution_mode 不是合法值
        :raises ConfigurationError: 异步模式下 func 不是协程函数
        """
        valid_modes = ("serial", "thread", "async")
        if execution_mode in valid_modes:
            self.execution_mode = execution_mode
        else:
            raise ExecutionModeError(execution_mode)

        if execution_mode == "async" and not inspect.iscoroutinefunction(self.func):
            raise ConfigurationError(
                f"execution_mode is 'async' but '{self.func.__name__}' is not a coroutine function"
            )

    def set_ctree(
        self, host: str = "127.0.0.1", http_port: int = 7777, grpc_port: int = 7778
    ) -> None:
        """
        设置 CelestialTreeClient

        :param host: 主机地址
        :param http_port: HTTP 端口
        :param grpc_port: gRPC 端口
        """
        self.ctree_client = CelestialTreeClient(
            host=host, http_port=http_port, grpc_port=grpc_port, transport="grpc"
        )

    def set_nullctree(
        self, ctree_client: NullCelestialTreeClient
    ) -> None:
        """
        设置NullCelestialTreeClient

        :param ctree_client: NullCelestialTreeClient 实例
        """
        self.ctree_client = ctree_client

    def set_name(self, name: str) -> None:
        """
        设置节点/管理器名称。

        :param name: 节点/管理器名称
        """
        self._name = name

    def set_log_level(self, log_level: str) -> None:
        """
        设置日志级别

        :param log_level: 日志级别
        """
        self.log_level = log_level.upper()

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
        获取当前节点的状态快照

        :return: 当前节点状态快照，
            包括执行器名称(name)、函数名(func_name)、类型名(class_name)、执行模式(execution_mode)
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

    def get_fallback_path(self) -> Path:
        """
        获取失败任务的回退路径

        :return: 失败任务持久化文件的绝对路径，未设置时返回空 Path
        """
        if self.fallback_spout.db_path is None:
            return Path()
        return Path(self.fallback_spout.db_path).resolve()

    def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
        """
        添加需要重试的异常类型

        :param exceptions: 异常类型
        """
        self.metrics.add_retry_exceptions(*exceptions)

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
        self.fallback_inlet.task_in(self.get_name(), input_id, task)
        self.log_inlet.task_input(
            self.get_func_name(),
            self._get_task_repr(task),
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
        self.log_inlet.termination_input(
            self.get_func_name(),
            self.get_name(),
            termination_id,
        )

    def _put_task_queue(self, task_source: Iterable[T]) -> None:
        """
        遍历任务源，逐个放入队列，末尾追加终止信号。

        :param task_source: 任务源（可迭代对象）
        """
        progress_num = 0
        for task in task_source:
            self.put_task(task)
            if self.metrics.get_task_count() % 100 == 0:
                self._notify("on_tasks_added", 100)
                progress_num += 100

        self._notify("on_tasks_added", self.metrics.get_task_count() - progress_num)
        self.put_signal()

    def _get_task_repr(self, task: T) -> str:
        """
        获取任务对象的可读字符串表示

        :param task: 任务对象
        :return: 任务信息字符串
        """
        return f"({format_repr(task, self.max_info)})"

    def _get_result_repr(self, result: Any) -> str:
        """
        获取结果信息

        :param result: 任务结果
        :return: 结果信息字符串
        """
        return f"({format_repr(result, self.max_info)})"

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
        self._notify("on_task_success")
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        result_id = self.ctree_client.emit(
            CTreeEvent.TASK_SUCCESS,
            parents=[task_id],
            payload=self.get_summary(),
        )

        self.metrics.add_success_count()
        self.fallback_inlet.task_success(task_id, result, persist=self.persist_result)

        self.log_inlet.task_success(
            self.get_func_name(),
            self._get_task_repr(task),
            self.execution_mode,
            self._get_result_repr(result),
            time.perf_counter() - start_time,
            task_id,
            result_id,
        )

        for target_name in self.result_queue.target_names:
            downstream_input_id = self.ctree_client.emit(
                CTreeEvent.TASK_INPUT,
                parents=[result_id],
                payload=self.get_summary(),
            )
            self.fallback_inlet.task_in(target_name, downstream_input_id, result)
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

        self.log_inlet.task_retry(
            self.get_func_name(),
            self._get_task_repr(task),
            retry_time,
            exception,
            task_id,
            retry_id,
        )
        self.fallback_inlet.task_retry(task_id, retry_id)

        return retry_envelope

    def handle_task_fail(
        self,
        task_envelope: TaskEnvelope[T],
        exception: Exception,
    ) -> None:
        """
        准备失败任务的结果信封

        :param task_envelope: 失败的任务
        :param exception: 捕获的异常
        """
        self._notify("on_task_fail")
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        error_id = self.ctree_client.emit(
            CTreeEvent.TASK_ERROR,
            parents=[task_id],
            payload=self.get_summary(),
        )

        self.metrics.add_error_count()

        self.fallback_inlet.task_fail(task_id, error_id, exception)
        self.log_inlet.task_error(
            self.get_func_name(),
            self._get_task_repr(task),
            exception,
            task_id,
            error_id,
        )

    def deal_duplicate(self, task_envelope: TaskEnvelope[T]) -> None:
        """
        处理重复任务

        :param task_envelope: 重复的任务
        """
        self._notify("on_task_duplicate")
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        self.metrics.add_duplicate_count()
        self.fallback_inlet.task_duplicate(task_id)
        duplicate_id = self.ctree_client.emit(
            CTreeEvent.TASK_DUPLICATE,
            parents=[task_id],
            payload=self.get_summary(),
        )
        self.log_inlet.task_duplicate(
            self.get_func_name(),
            self._get_task_repr(task),
            task_id,
            duplicate_id,
        )

    # ==== 启动 ====
    def _prepare_start(self, task_source: Iterable[T]) -> float:
        """
        启动前准备：初始化环境、注入任务、记录启动日志。

        :param task_source: 任务源
        :return: 启动时间戳
        """
        start_time = time.perf_counter()
        self.init_env()

        self._notify("on_start", self.get_full_name(), 0)
        self._put_task_queue(task_source)
        self.log_inlet.start_executor(
            self.get_name(),
            self.metrics.get_task_count(),
            self._get_execution_mode_desc(),
        )
        return start_time

    def _finish_start(self, start_time: float) -> None:
        """
        启动后清理：释放客户端、记录结束日志、停止 spout。

        :param start_time: 启动时的时间戳
        """
        self._notify("on_finish")
        self.log_inlet.end_executor(
            self.get_name(),
            self._get_execution_mode_desc(),
            time.perf_counter() - start_time,
            self.metrics.get_success_count(),
            self.metrics.get_error_count(),
            self.metrics.get_duplicate_count(),
        )
        self.log_spout.stop()
        self.fallback_spout.stop()

    def start(self, task_source: Iterable[T]) -> None:
        """
        根据 execution_mode 的值，选择串行、线程或异步执行任务。

        :param task_source: 任务迭代器或者生成器
        :raises ExecutionModeError: execution_mode 为非法值时触发
        :note:
            TaskExecutor 为一次性对象；当前实例完成一次 start() 后，不保证可安全再次
            调用 start()。如需再次执行，请创建新的 TaskExecutor。
        """
        start_time = self._prepare_start(task_source)
        try:
            if self.execution_mode == "thread":
                self.dispatch.dispatch_thread()
            elif self.execution_mode == "serial":
                self.dispatch.dispatch_serial()
            elif self.execution_mode == "async":
                asyncio.run(self.dispatch.dispatch_async())
            else:
                raise ExecutionModeError(self.execution_mode)
        finally:
            self._finish_start(start_time)

    async def start_async(self, task_source: Iterable[T]) -> None:
        """
        异步地执行任务。

        :param task_source: 任务迭代器或者生成器
        :note:
            TaskExecutor 为一次性对象；当前实例完成一次 start_async() 后，不保证可
            安全再次调用。需要重复执行时请创建新的 TaskExecutor。
        """
        self.set_execution_mode("async")
        start_time = self._prepare_start(task_source)
        try:
            await self.dispatch.dispatch_async()
        finally:
            self._finish_start(start_time)

    def start_db(self, db_path: str | Path, status: str = "failed") -> None:
        """
        从 sqlite 持久化库中读取当前 stage 的失败任务并启动执行。

        :param db_path: sqlite 数据库文件路径
        :param status: 记录状态过滤条件，默认 ``failed``
        """
        grouped_records = load_records_grouped_by_stage(db_path, status)
        records = grouped_records.get(self.get_name(), [])
        executor_tasks = [cast(T, record["task"]) for record in records]

        self.start(executor_tasks)

    # ==== 结果获取 ====
    def get_success_pairs(self) -> list[tuple[T, R]]:
        """
        获取成功任务的列表

        :return: (task, result) 元组列表
        """
        if not self.persist_result:
            warnings.warn(
                (
                    "get_success_pairs() is not available when persist_result is False."
                    "Please set persist_result to True to get success pairs."
                ),
                stacklevel=2,
            )
            return []
        return self.fallback_spout.get_task_result_pairs(self.get_name())

    def get_error_pairs(self) -> list[tuple[T, PersistedError]]:
        """
        获取出错任务的列表

        :return: (task, PersistedError) 元组列表
        """
        task_error_pairs = self.fallback_spout.get_task_error_pairs(self.get_name())
        return [
            (task, PersistedError(error_type, error_message))
            for task, (error_type, error_message) in task_error_pairs
        ]
