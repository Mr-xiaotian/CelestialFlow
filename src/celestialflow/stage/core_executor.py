# stage/core_executor.py
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from collections.abc import Iterable
from multiprocessing import Queue as MPQueue
from queue import Queue as ThreadQueue
from typing import Any, Callable

from celestialtree import (
    Client as CelestialTreeClient,
)
from celestialtree import (
    NullClient as NullCelestialTreeClient,
)

from ..observability import BaseObserver
from ..persistence import FailInlet, FailSpout, LogInlet, LogSpout, SuccessSpout
from ..runtime import (
    TaskDispatch,
    TaskEnvelope,
    TaskInQueue,
    TaskMetrics,
    TaskOutQueue,
)
from ..runtime.util_errors import ExecutionModeError
from ..runtime.util_factories import (
    make_queue_backend,
    make_task_in_queue,
    make_task_out_queue,
)
from ..runtime.util_types import (
    CTreeEvent,
    TerminationSignal,
)
from ..utils.util_format import format_repr


class TaskExecutor:
    """任务执行器基类，支持串行、线程和异步三种执行模式。"""

    # ==== 初始化 ====
    def __init__(
        self,
        name: str,
        func: Callable,
        execution_mode: str = "serial",
        max_workers: int = 20,
        max_retries: int = 1,
        max_info: int = 50,
        unpack_task_args: bool = False,
        enable_duplicate_check: bool = True,
        log_level: str = "SUCCESS",
    ):
        """
        初始化 TaskExecutor

        :param name: 节点/管理器名称
        :param func: 可调用对象
        :param execution_mode: 执行模式，可选 'serial', 'thread', 'async'
        :param max_workers: 同时处理数量
        :param max_retries: 任务的最大重试次数, 默认值为 1，表示每个任务最多执行两次（一次正常执行 + 一次重试）
        :param max_info: 日志中每条信息的最大长度
        :param unpack_task_args: 是否将任务参数解包
        :param enable_duplicate_check: 是否启用重复检查
        :param log_level: 日志级别
        """

        self.set_name(name)
        self._set_func(func)

        self.set_execution_mode(execution_mode)
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.max_info = max_info
        self.unpack_task_args = unpack_task_args
        self.enable_duplicate_check = enable_duplicate_check
        self.set_log_level(log_level)

        self._observers: list[BaseObserver] = []

        self.set_nullctree()
        self.task_queues: TaskInQueue = None
        self.result_queues: TaskOutQueue = None
        self.fail_queue: Any = None
        self.log_queue: Any = None
        self._init_metrics()

    def _init_metrics(self) -> None:
        """
        初始化任务指标
        """
        self.metrics = TaskMetrics(
            execution_mode=self.execution_mode,
            max_retries=self.max_retries,
            enable_duplicate_check=self.enable_duplicate_check,
        )

    def init_env(
        self,
        task_queues: TaskInQueue | None = None,
        result_queues: TaskOutQueue | None = None,
        fail_queue: MPQueue | None = None,
        log_queue: MPQueue | None = None,
    ) -> None:
        """
        初始化环境

        :param task_queues: 任务队列列表
        :param result_queues: 结果队列列表
        :param fail_queue: 失败队列
        :param log_queue: 日志队列
        """
        self._init_state()
        self._init_inlet(fail_queue, log_queue)
        self._init_queue(task_queues, result_queues)
        self._init_dispatch()

    def _init_state(self) -> None:
        """
        初始化任务状态
        """
        self.metrics.reset_state()

    def _init_inlet(
        self, fail_queue: MPQueue | None, log_queue: MPQueue | None
    ) -> None:
        """
        初始化收集器

        :param fail_queue: 失败队列
        :param log_queue: 日志队列
        """
        self.fail_queue = fail_queue or make_queue_backend("serial")()
        self.fail_inlet = FailInlet(self.fail_queue)

        self.log_queue = log_queue or make_queue_backend("serial")()
        self.log_inlet = LogInlet(self.log_queue, self.log_level)

    def _init_queue(
        self,
        task_queues: TaskInQueue | None = None,
        result_queues: TaskOutQueue | None = None,
    ) -> None:
        """
        初始化队列

        :param task_queues: 任务队列列表
        :param result_queues: 结果队列列表
        """
        mode = self.execution_mode

        if task_queues is not None:
            self.task_queues = task_queues
        else:
            queue = ThreadQueue()
            self.task_queues = make_task_in_queue(
                queue=queue,
                executor=self,
            )
        if result_queues is not None:
            self.result_queues = result_queues
        else:
            self.result_queues = make_task_out_queue(
                queue=self.success_spout.get_queue(),
                executor=self,
            )

    def _init_dispatch(self) -> None:
        """
        初始化任务运行器
        """
        self.dispatch = TaskDispatch(self, self.func, self.max_workers)

    def _init_spout(self) -> None:
        """
        初始化监听器
        """
        self.fail_spout = FailSpout("executor_errors")
        self.log_spout = LogSpout()
        self.success_spout = SuccessSpout()

        self.fail_spout.start()
        self.log_spout.start()
        self.success_spout.start()

    # ==== Observer ====
    def add_observer(self, observer: BaseObserver) -> None:
        self._observers.append(observer)

    def remove_observer(self, observer: BaseObserver) -> None:
        self._observers.remove(observer)

    def _notify(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        for observer in self._observers:
            getattr(observer, method_name)(*args, **kwargs)

    # ==== 配置 ====
    def _set_func(self, func: Callable) -> None:
        """
        设置执行函数

        :param func: 执行函数
        """
        self.func = func
        self._func_name = func.__name__

    def set_execution_mode(self, execution_mode: str) -> None:
        """
        设置执行模式

        :param execution_mode: 执行模式，可以是 'thread'（线程）, 'async'（异步）, 'serial'（串行）
        """
        valid_modes = ("serial", "thread", "async")
        if execution_mode in valid_modes:
            self.execution_mode = execution_mode
        else:
            raise ExecutionModeError(execution_mode)

        if getattr(
            self, "execution_mode", None
        ) == "async" and not asyncio.iscoroutinefunction(self.func):
            raise RuntimeError(
                f"execution_mode is 'async' but '{self.func.__name__}' is not a coroutine function"
            )

        if hasattr(self, "metrics"):
            self.metrics.set_execution_mode(execution_mode)

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

    def set_nullctree(self, event_id: int | None = None) -> None:
        """
        设置NullCelestialTreeClient

        :param event_id: 事件ID
        """
        self.ctree_client = NullCelestialTreeClient(event_id)

    def set_name(self, name: str) -> None:
        self._name = name
        if hasattr(self, "_tag"):
            delattr(self, "_tag")

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

    def get_tag(self) -> str:
        """
        获取当前节点/管理器标签

        :return: 当前节点/管理器标签
        """
        if hasattr(self, "_tag"):
            return str(self._tag)
        self._tag: str = f"{self.get_name()}[{self.get_func_name()}]"
        return self._tag

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

    def get_summary(self) -> dict:
        """
        获取当前节点的状态快照

        :return: 当前节点状态快照，
            包括执行器名称(name)、函数名(func_name)、类型名(class_name)、执行模式(execution_mode)
        """
        return {
            "name": self.get_name(),
            "func_name": self.get_func_name(),
            "class_name": self._get_class_name(),
            "execution_mode": self._get_execution_mode_desc(),
        }

    def get_counts(self) -> dict:
        """
        获取当前节点的计数器

        :return: 当前节点计数器
        包括 tasks_input, tasks_succeeded, tasks_failed, tasks_duplicated, tasks_processed, tasks_pending
        """
        return self.metrics.get_counts()

    def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
        """
        添加需要重试的异常类型

        :param exceptions: 异常类型
        """
        self.metrics.add_retry_exceptions(*exceptions)

    # ==== 任务输入 ====
    def _prepare_task_envelopes(
        self, task_source: Iterable
    ) -> list[TaskEnvelope | TerminationSignal]:
        """
        构建所有任务信封和终止信号，返回待入队列表。

        :param task_source: 任务源
        :return: 待入队的 TaskEnvelope 和 TerminationSignal 列表
        """
        items: list[TaskEnvelope | TerminationSignal] = []
        progress_num = 0

        for task in task_source:
            input_id = self.ctree_client.emit(
                CTreeEvent.TASK_INPUT,
                payload=self.get_summary(),
            )
            envelope = TaskEnvelope(task, input_id, source="input")
            items.append(envelope)
            self.metrics.add_task_count()
            self.log_inlet.task_input(
                self.get_func_name(),
                self.get_task_repr(task),
                self.get_tag(),
                input_id,
            )

            if self.metrics.get_task_count() % 100 == 0:
                self._notify("on_tasks_added", 100)
                progress_num += 100

        self._notify("on_tasks_added", self.metrics.get_task_count() - progress_num)

        termination_id = self.ctree_client.emit(
            CTreeEvent.TERMINATION_INPUT,
            payload=self.get_summary(),
        )
        items.append(TerminationSignal(termination_id, source="input"))
        self.log_inlet.termination_input(
            self.get_func_name(),
            self.get_tag(),
            termination_id,
        )
        return items

    def _put_task_queues(self, task_source: Iterable) -> None:
        """
        将任务放入任务队列

        :param task_source: 任务源（可迭代对象）
        """
        for item in self._prepare_task_envelopes(task_source):
            self.task_queues.put(item)

    def get_args(self, task: Any) -> tuple:
        """
        从 obj 中获取参数。可根据需要覆写
        在这个示例中，我们根据 unpack_task_args 决定是否解包参数

        :param task: 任务对象
        :return: 任务参数元组
        """
        if self.unpack_task_args:
            return task
        return (task,)

    def process_result(self, task: Any, result: Any) -> Any:
        """
        从结果队列中获取结果，并进行处理。可根据需要覆写
        在这个示例中，我们只是简单地返回结果

        :param task: 任务对象
        :param result: 任务结果
        :return: 处理后的结果
        """
        return result

    def process_result_dict(self) -> dict[Any, Any]:
        """
        处理结果列表。可根据需要覆写

        :return: 处理后的结果列表
        """
        result_dict = dict()
        for task, result in self.get_success_pairs():
            result_dict[task] = result
        for task, error in self.get_error_pairs():
            result_dict[task] = str(error)
        return result_dict

    def handle_error_dict(self) -> dict[Any, list]:
        """
        处理错误字典。可根据需要覆写

        在这个示例中，我们将列表合并为错误组
        """
        error_groups = defaultdict(list)
        for task, error in self.get_error_pairs():
            error_groups[error].append(task)

        return dict(error_groups)  # 转换回普通字典

    def get_task_repr(self, task: Any) -> str:
        """
        获取任务参数信息的可读字符串表示

        :param task: 任务对象
        :return: 任务参数信息字符串
        """
        args = self.get_args(task)

        # 格式化每个参数
        def format_args_list(args_list: Any) -> list[str]:
            """
            将参数列表格式化为可读字符串列表。

            :param args_list: 原始参数列表
            :return: 格式化后的字符串列表
            """
            return [format_repr(arg, self.max_info) for arg in args_list]

        if len(args) <= 3:
            formatted_args = format_args_list(args)
        else:
            # 显示前两个 + ... + 最后一个
            head = format_args_list(args[:2])
            tail = format_args_list([args[-1]])
            formatted_args = head + ["..."] + tail

        return f"({', '.join(formatted_args)})"

    def _get_result_repr(self, result: Any) -> str:
        """
        获取结果信息

        :param result: 任务结果
        :return: 结果信息字符串
        """
        formatted_result = format_repr(result, self.max_info)
        return f"{formatted_result}"

    # ==== 结果处理 ====
    def process_task_success(
        self, task_envelope: TaskEnvelope, result: Any, start_time: float
    ) -> None:
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        self._notify("on_task_success")
        task = task_envelope.task
        task_id = task_envelope.id

        processed_result = self.process_result(task, result)

        result_id = self.ctree_client.emit(
            CTreeEvent.TASK_SUCCESS,
            parents=[task_id],
            payload=self.get_summary(),
        )
        result_envelope = TaskEnvelope(
            processed_result,
            result_id,
            source=self.get_tag(),
            prev=task,
        )

        self.metrics.add_success_count()

        self.log_inlet.task_success(
            self.get_func_name(),
            self.get_task_repr(task),
            self.execution_mode,
            self._get_result_repr(result),
            time.perf_counter() - start_time,
            task_id,
            result_id,
        )

        self.result_queues.put(result_envelope)

    def emit_retry_envelope(
        self,
        task_envelope: TaskEnvelope,
        exception: Exception,
        retry_time: int,
    ) -> TaskEnvelope:
        """
        为重试任务生成新的信封 ID 并记录日志

        :param task_envelope: 发生异常的任务
        :param exception: 捕获的异常
        :param retry_time: 当前重试次数
        :return: 更新后的任务信封
        """
        task_id = task_envelope.get_id()

        retry_id = self.ctree_client.emit(
            f"{CTreeEvent.TASK_RETRY_PREFIX}{retry_time}",
            parents=[task_id],
            payload=self.get_summary(),
        )
        task_envelope.change_id(retry_id)

        self.log_inlet.task_retry(
            self.get_func_name(),
            self.get_task_repr(task_envelope.task),
            retry_time,
            exception,
            task_id,
            retry_id,
        )

        return task_envelope

    def handle_task_fail(
        self,
        task_envelope: TaskEnvelope,
        exception: Exception,
    ) -> TaskEnvelope:
        """
        准备失败任务的结果信封

        :param task_envelope: 失败的任务
        :param exception: 捕获的异常
        :return: 失败任务的结果信封
        """
        self._notify("on_task_fail")

        error_id = self.ctree_client.emit(
            CTreeEvent.TASK_ERROR,
            parents=[task_envelope.id],
            payload=self.get_summary(),
        )

        task_id = task_envelope.get_id()
        self.metrics.add_error_count()

        self.fail_inlet.task_error(
            self.get_tag(), exception, error_id, task_envelope.task
        )
        self.log_inlet.task_error(
            self.get_func_name(),
            self.get_task_repr(task_envelope.task),
            exception,
            task_id,
            error_id,
        )
        return task_envelope

    def deal_duplicate(self, task_envelope: TaskEnvelope) -> None:
        """
        处理重复任务

        :param task_envelope: 重复的任务
        """
        self._notify("on_task_duplicate")
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        self.metrics.add_duplicate_count()
        duplicate_id = self.ctree_client.emit(
            CTreeEvent.TASK_DUPLICATE,
            parents=[task_id],
            payload=self.get_summary(),
        )
        self.log_inlet.task_duplicate(
            self.get_func_name(),
            self.get_task_repr(task),
            task_id,
            duplicate_id,
        )

    # ==== 启动 ====
    def start(self, task_source: Iterable) -> None:
        """
        根据 execution_mode 的值，选择串行、线程或异步执行任务

        :param task_source: 任务迭代器或者生成器
        """
        start_time = time.perf_counter()
        self._init_spout()
        self.init_env(
            log_queue=self.log_spout.get_queue(),
            fail_queue=self.fail_spout.get_queue(),
        )

        self._notify("on_start", self.get_full_name(), 0)
        self._put_task_queues(task_source)
        self.fail_inlet.start_executor(self.get_tag())
        self.log_inlet.start_executor(
            self.get_name(),
            self.get_func_name(),
            self.metrics.get_task_count(),
            self._get_execution_mode_desc(),
        )

        try:
            # 根据模式运行对应的任务处理函数
            if self.execution_mode == "thread":
                self.dispatch.dispatch_thread()
            elif self.execution_mode == "async":
                # don't suggest, please use start_async
                asyncio.run(self.dispatch.dispatch_async())
            elif self.execution_mode == "serial":
                self.dispatch.dispatch_serial()
            else:
                raise ExecutionModeError(self.execution_mode)

        finally:
            self._release_client()

            self._notify("on_finish")
            self.log_inlet.end_executor(
                self.get_name(),
                self.get_func_name(),
                self.execution_mode,
                time.perf_counter() - start_time,
                self.metrics.get_success_count(),
                self.metrics.get_error_count(),
                self.metrics.get_duplicate_count(),
            )
            self.log_spout.stop()
            self.fail_spout.stop()
            self.success_spout.stop()

    async def start_async(self, task_source: Iterable) -> None:
        """
        异步地执行任务

        :param task_source: 任务迭代器或者生成器
        """
        start_time = time.perf_counter()
        self.set_execution_mode("async")
        self._init_spout()
        self.init_env(
            log_queue=self.log_spout.get_queue(),
            fail_queue=self.fail_spout.get_queue(),
        )

        self._notify("on_start", self.get_full_name(), 0)
        self._put_task_queues(task_source)
        self.log_inlet.start_executor(
            self.get_name(),
            self.get_func_name(),
            self.metrics.get_task_count(),
            self._get_execution_mode_desc(),
        )
        self.fail_inlet.start_executor(self.get_tag())

        try:
            await self.dispatch.dispatch_async()

        finally:
            self._release_client()

            self._notify("on_finish")
            self.log_inlet.end_executor(
                self.get_name(),
                self.get_func_name(),
                self.execution_mode,
                time.perf_counter() - start_time,
                self.metrics.get_success_count(),
                self.metrics.get_error_count(),
                self.metrics.get_duplicate_count(),
            )
            self.log_spout.stop()
            self.fail_spout.stop()
            self.success_spout.stop()

    # ==== 清理 ====
    def get_success_pairs(self) -> list[tuple[Any, Any]]:
        """
        获取成功任务的列表

        :return: (task, result) 元组列表
        """
        return self.success_spout.get_success_pairs()

    def get_error_pairs(self) -> list[tuple[Any, Exception]]:
        """
        获取出错任务的列表

        :return: (task, exception) 元组列表
        """
        return self.fail_spout.get_error_pairs()

    def release_queue(self) -> None:
        """释放任务队列、结果队列和失败队列的引用"""
        self.task_queues = None
        self.result_queues = None
        self.fail_queue = None

    def _release_client(self) -> None:
        """释放事件树客户端引用"""
        self.ctree_client = None
