# node/core_node.py
from __future__ import annotations

import inspect
import os
import time
from collections.abc import Awaitable, Callable, Iterable
from pathlib import Path
from typing import Any, cast

from ..observer import (
    NodeEndEvent,
    NodeStartEvent,
    Observer,
    ObserverHub,
    TaskFailEvent,
    TaskInputEvent,
    TaskRetryEvent,
    TaskSkipEvent,
    TerminationInputEvent,
)
from ..persist import run_resources
from ..persist.util_sqlite import (
    load_task_error_records,
    load_task_result_records,
    load_tasks_grouped_by_node,
)
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
from ..runtime.util_event import EventClient, LocalEventClient
from ..runtime.util_format import format_repr
from ..runtime.util_types import (
    CTreeEvent,
    TerminationSignal,
    ValueWrapper,
)
from .core_dispatch import TaskDispatch
from .util_callable import validate_executor_func_signature


class BaseTaskNode[T, R, Y]:
    """任务节点基类，支持串行、线程和异步三种执行模式。

    注意：
    - ``start()`` / ``start_async()`` 为一次性调用；启动并运行完成后，不保证当前实例可被
      安全重置并再次复用。如需重复执行同一逻辑，请重新创建新的 BaseTaskNode 实例。
    - 启动前的 setter（``set_execution_mode`` / ``set_retry_exceptions`` / ``set_ctree`` /
      ``add_observer`` 等）允许在 start 之前多次调用。
    - 任务输入/结果队列、metrics 状态与 ctree 客户端由节点自身持有；全局
      ``LifecycleSpout`` / ``LogSpout`` 的启停与全局 funnel 观察者的注册由
      :meth:`run` / :meth:`run_async` 统一负责，BaseTaskNode 自身不直接持有
      spout 实例。
    """

    # ==== 类级类型注解 ====

    _name: str
    task_queue: TaskInQueue[T]
    yield_queue: TaskOutQueue[Y]
    max_workers: int
    max_retries: int
    max_info: int
    metrics: TaskMetrics
    dispatch: TaskDispatch[T, R, Y]
    execution_mode: str
    func: Callable[[T], R] | Callable[[T], Awaitable[R]]
    skip_func: Callable[[T], bool] | None
    ctree_client: EventClient
    observers: ObserverHub
    _downstream_nodes: dict[str, BaseTaskNode[Any, Any, Any]]
    _lifecycle_db_path: Path | None

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
        skip_func: Callable[[T], bool] | None = None,
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
        :param skip_func: 任务跳过判定函数，接受单个任务参数并返回 ``bool``；
            返回 ``True`` 时该任务不执行 ``func`` 而直接记为跳过，默认 ``None`` 表示不跳过任何任务
        :note:
            ``start()`` / ``start_async()`` 为一次性调用；启动前的 setter 与 observer
            注册允许重复调用。
        """

        self.set_name(name)
        self._set_func(func)
        self.set_skip_func(skip_func)

        self.set_execution_mode(execution_mode)
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.max_retries = max_retries
        self.max_queue_size = max_queue_size
        self.max_info = max_info

        self.set_ctree(LocalEventClient())

        # IDE 类型检查器会把这里的 ``self`` 视为更宽的 ``Self``，
        # 显式收窄为 ``BaseTaskNode[T, R, Y]`` 可避免初始化阶段的误报。
        self.dispatch = TaskDispatch(
            cast(BaseTaskNode[T, R, Y], self), self.func, self.max_workers
        )
        self.task_queue = TaskInQueue(
            out_name=self.get_name(),
            maxsize=self.max_queue_size,
        )
        self.yield_queue = TaskOutQueue(
            in_name=self.get_name(),
        )
        self.metrics = TaskMetrics()
        self.observers = ObserverHub()
        self._downstream_nodes = {}
        self._lifecycle_db_path = None

        # 上报器可能会在节点真正启动前先采集一次快照。
        self.start_time = 0.0

    # ==== 观察者 ====
    def add_observer(self, observer: Observer) -> None:
        """
        注册观察者。

        :param observer: 要注册的观察者实例
        """
        self.observers.add_observer(observer)

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

    def set_skip_func(self, skip_func: Callable[[T], bool] | None) -> None:
        """
        设置任务跳过判定函数。

        :param skip_func: 接受单个任务参数并返回 ``bool`` 的判定函数；
            ``True`` 表示该任务应被跳过；``None`` 表示不跳过任何任务
        :raises ConfigurationError: 判定函数未接受恰好一个位置参数
        :raises CallableParameterKindError: 判定函数包含 VAR/KEYWORD 参数
        """
        if skip_func is None:
            self.skip_func = None
            return

        parameter_count = validate_executor_func_signature(skip_func)
        if parameter_count != 1:
            raise ConfigurationError(
                f"BaseTaskNode skip_func '{getattr(skip_func, '__name__', type(skip_func).__name__)}' "
                "must accept exactly one positional task argument."
            )

        self.skip_func = skip_func

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

    def get_meta(self) -> dict[str, Any]:
        """
        获取节点的构建期元信息。

        这些字段在 reporter 启动前已冻结，随图结构一次性上报；与每轮采集的
        :meth:`get_snapshot` 区分开，避免在状态推送里重复传输。

        :return: 包含 ``class_name``、``execution_mode`` 与 ``max_workers`` 的字典
        """
        return {
            "class_name": self._get_class_name(),
            "execution_mode": self.execution_mode,
            "max_workers": self.max_workers,
        }

    def get_snapshot(self) -> dict[str, Any]:
        """
        采集当前节点的运行时快照。

        忙碌耗时由 :class:`TaskMetrics` 在任务实际执行期间自行累计，
        因此无需调用方传入快照间隔。

        :return: 包含状态、计数、耗时估算等信息的快照字典
        """
        return {
            "start_time": self.start_time,
            "status": self.metrics.get_status(),
            "elapsed_time": self.metrics.get_elapsed(),
            **self.metrics.get_counts(),
            "upstream_counts": self.metrics.get_upstream_counts(),
            "downstream_counts": self.metrics.get_downstream_counts(),
        }

    # ==== 绑定 ====

    def connect_to(self, next_node: BaseTaskNode[Any, Any, Any]) -> None:
        """
        绑定下游节点，将当前节点注册为其前置节点。

        双方共享同一个传输计数计数器：当前节点向下游每发送一个任务，计数器递增，
        下游节点的上游提供任务数随之增加。

        :param next_node: 下游节点
        """
        counter = ValueWrapper(value=0)
        self.metrics.set_downstream_counter(next_node.get_name(), counter)
        next_node.metrics.set_upstream_counter(self.get_name(), counter)

        self._downstream_nodes[next_node.get_name()] = next_node
        self.yield_queue.add_queue(next_node.get_name(), next_node.task_queue)
        next_node.task_queue.add_source_name(self.get_name())

    def _notify_downstream_input(
        self,
        target_name: str,
        task: Any,
        task_repr: str,
        input_id: int,
    ) -> None:
        """
        向接收方节点分发“上游输入”事件。

        若目标名称只绑定了裸队列（未通过 ``connect_to`` 关联节点），则忽略。

        :param target_name: 接收任务的节点名称
        :param task: 原始任务数据
        :param task_repr: 任务的可读表示
        :param input_id: 任务在接收方的事件 ID
        """
        node = self._downstream_nodes.get(target_name)
        if node is None:
            return
        node.observers.on_task_input(
            TaskInputEvent(
                node=target_name,
                task=task,
                task_repr=task_repr,
                input_id=input_id,
                source="upstream",
            )
        )

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
        self.metrics.add_external_input_count(1)

        task_repr = self._get_repr(task)
        self.observers.on_task_input(
            TaskInputEvent(
                node=self.get_name(),
                task=task,
                task_repr=task_repr,
                input_id=input_id,
                source="external",
            )
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
        self.observers.on_termination_input(
            TerminationInputEvent(
                node=self.get_name(),
                termination_id=termination_id,
            )
        )

    def drain_task_queue(self) -> None:
        """清空任务队列，将所有任务移至失败队列。"""
        remaining_sources = self.task_queue.drain()

        # 持久化逻辑
        for source in remaining_sources:
            self.handle_task_fail(source, UnconsumedError())

    def _get_repr(self, task: T | R | Y) -> str:
        """
        获取任务/结果对象的可读字符串表示

        :param task: 任务对象
        :return: 任务信息字符串
        """
        return f"({format_repr(task, self.max_info)})"

    # ==== 结果处理 ====

    def process_task_success(
        self, task_envelope: TaskEnvelope[T], result: R, start_perf: float
    ) -> None:
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_perf: 任务开始时间
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

        self.metrics.add_fail_count(1)

        task_repr = self._get_repr(task)
        self.observers.on_task_fail(
            TaskFailEvent(
                node=self.get_name(),
                task=task,
                task_repr=task_repr,
                exception=exception,
                task_id=task_id,
                error_id=error_id,
            )
        )

    def handle_task_skip(self, task_envelope: TaskEnvelope[T]) -> None:
        """
        记录被跳过的任务：发布跳过事件并持久化跳过信息。

        :param task_envelope: 被跳过的任务
        """
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        skip_id = self.ctree_client.emit(
            CTreeEvent.TASK_SKIP,
            parents=[task_id],
        )

        self.metrics.add_skip_count(1)

        task_repr = self._get_repr(task)
        self.observers.on_task_skip(
            TaskSkipEvent(
                node=self.get_name(),
                task=task,
                task_repr=task_repr,
                task_id=task_id,
                skip_id=skip_id,
            )
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

        self.observers.on_task_retry(
            TaskRetryEvent(
                node=self.get_name(),
                task=task,
                task_repr=self._get_repr(task),
                exception=exception,
                task_id=task_id,
                retry_times=fail_times,
            )
        )

    # ==== 执行 ====

    def run(
        self,
        task_source: Iterable[T],
        *,
        if_put_signal: bool = True,
    ) -> None:
        """
        执行任务。

        本方法负责实例化运行期资源：注册全局 funnel 观察者、启动全局
        ``lifecycle`` / ``log`` spout，注入任务后交由 :meth:`start` 处理，
        最后统一收尾。

        :param task_source: 任务源
        :param if_put_signal: 是否注入终止信号，默认 True
        :return: ``None``
        """
        error_list: list[Exception] = []

        try:
            with run_resources(self.observers) as lifecycle_db_path:
                self._lifecycle_db_path = lifecycle_db_path
                for task in task_source:
                    self.put_task(task)
                if if_put_signal:
                    self.put_signal()
                self.start()
        except Exception as exception:
            error_list.append(exception)

        if error_list:
            raise ExceptionGroup("Errors occurred during run", error_list)

    async def run_async(
        self,
        task_source: Iterable[T],
        *,
        if_put_signal: bool = True,
    ) -> None:
        """
        异步启动任务节点。

        运行期资源的实例化与收尾同 :meth:`run`，区别仅在于以协程方式启动。

        :param task_source: 任务源
        :param if_put_signal: 是否注入终止信号，默认 True
        :return: ``None``
        """
        error_list: list[Exception] = []

        try:
            with run_resources(self.observers) as lifecycle_db_path:
                self._lifecycle_db_path = lifecycle_db_path
                for task in task_source:
                    self.put_task(task)
                if if_put_signal:
                    self.put_signal()
                await self.start_async()
        except Exception as exception:
            error_list.append(exception)

        if error_list:
            raise ExceptionGroup("Errors occurred during run", error_list)

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
        grouped_tasks = load_tasks_grouped_by_node(db_path, statuses)
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
        启动前准备：重置运行期状态并广播启动事件。

        :return: ``None``
        """
        self.metrics.on_start()

        self.observers.on_node_start(
            NodeStartEvent(
                node=self.get_name(),
                execution_mode=self.execution_mode,
                max_workers=self.max_workers,
                task_count=self.metrics.get_input_count(),
            )
        )

    def _finish_start(self, start_perf: float) -> list[Exception]:
        """
        启动后清理：广播执行结束事件。

        :param start_perf: 启动时的时间戳
        """
        error_list: list[Exception] = []
        elapsed = time.perf_counter() - start_perf

        try:
            self.observers.on_node_end(
                NodeEndEvent(
                    node=self.get_name(),
                    execution_mode=self.execution_mode,
                    max_workers=self.max_workers,
                    elapsed=elapsed,
                    succeeded=self.metrics.get_success_count(),
                    failed=self.metrics.get_fail_count(),
                    skipped=self.metrics.get_skip_count(),
                )
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
            error_list.append(exception)
        finally:
            error_list.extend(self._finish_start(start_perf))

        if error_list:
            raise ExceptionGroup("Errors occurred during execution", error_list)

    # ==== 结果获取 ====

    def get_success_pairs(self) -> list[tuple[T, R]]:
        """
        获取成功任务的列表。

        仅在本节点通过 :meth:`run` / :meth:`run_async` 独立运行时可用；
        由图级调度（:class:`~celestialflow.graph.core_graph.TaskGraph`）统一运行时，
        记录落在图级 lifecycle 库，本方法返回空列表。

        :return: (task, result) 元组列表；无 lifecycle 库时为空
        """
        if self._lifecycle_db_path is None:
            return []
        return load_task_result_records(self._lifecycle_db_path, self.get_name())

    def get_error_pairs(self) -> list[tuple[T, PersistedError]]:
        """
        获取出错任务的列表。

        可用条件同 :meth:`get_success_pairs`，节点未独立运行时返回空列表。

        :return: (task, PersistedError) 元组列表；无 lifecycle 库时为空
        """
        if self._lifecycle_db_path is None:
            return []
        task_error_pairs = load_task_error_records(
            self._lifecycle_db_path, self.get_name()
        )
        return [
            (task, PersistedError(error_type, error_message))
            for task, (error_type, error_message) in task_error_pairs
        ]
