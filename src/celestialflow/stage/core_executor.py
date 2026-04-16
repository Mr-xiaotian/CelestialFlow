# stage/core_executor.py
from __future__ import annotations

import asyncio
import time
import warnings
from collections import defaultdict
from collections.abc import Iterable
from multiprocessing import Queue as MPQueue
from typing import Any, Callable

from celestialtree import (
    Client as CelestialTreeClient,
)
from celestialtree import (
    NullClient as NullCelestialTreeClient,
)

from ..observability import TaskProgress, NullTaskProgress
from ..persistence import FailSpout, FailInlet, LogSpout, LogInlet
from ..persistence.util_jsonl import load_task_error_pairs
from ..runtime import (
    TaskEnvelope,
    TaskInQueue,
    TaskMetrics,
    TaskOutQueue,
    TaskDispatch,
)
from ..runtime.util_errors import ExecutionModeError
from ..runtime.util_factories import (
    make_queue_backend,
    make_task_in_queue,
    make_task_out_queue,
)
from ..runtime.util_types import (
    TerminationSignal,
)
from ..utils.util_format import format_repr


class TaskExecutor:
    _name = "Executor"

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
        show_progress=False,
        progress_desc="Executing",
        log_level="SUCCESS",
    ):
        """
        初始化 TaskExecutor

        :param func: 可调用对象
        :param execution_mode: 执行模式，可选 'serial', 'thread', 'process', 'async' (组合为 'TaskGraph' 时不可用 'process' 和 'async' 模式)
        :param max_workers: 同时处理数量
        :param max_retries: 任务的最大重试次数
        :param max_info: 日志中每条信息的最大长度
        :param unpack_task_args: 是否将任务参数解包
        :param enable_success_cache: 是否启用成功结果缓存, 将成功结果保存在 success_pairs 中
        :param enable_duplicate_check: 是否启用重复检查
        :param progress_desc: 进度条显示名称
        :param show_progress: 进度条显示与否
        """
        if enable_success_cache == True and enable_duplicate_check == False:
            warnings.warn(
                "Result cache is enabled while duplicate check is disabled. "
                "This may cause the number of cached results to differ from the number of input tasks "
                "due to duplicated task execution.",
                RuntimeWarning,
            )

        self.set_func(func)
        self.set_execution_mode(execution_mode)
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.max_info = max_info

        self.unpack_task_args = unpack_task_args
        self.enable_success_cache = enable_success_cache
        self.enable_duplicate_check = enable_duplicate_check

        self.show_progress = show_progress
        self.progress_desc = progress_desc
        self.set_log_level(log_level)

        self.ctree_client: Any = None
        self.task_queues: TaskInQueue | None = None
        self.result_queues: TaskOutQueue | None = None
        self.fail_queue: Any = None
        self.log_queue: Any = None
        self.init_metrics()

    def init_metrics(self) -> None:
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
        fail_queue=None,
        log_queue=None,
    ) -> None:
        """
        初始化环境

        :param task_queues: 任务队列列表
        :param result_queues: 结果队列列表
        :param fail_queue: 失败队列
        :param log_queue: 日志队列
        """
        self.init_state()
        self.init_inlet(fail_queue, log_queue)
        self.init_queue(task_queues, result_queues)
        self.init_dispatch()

    def init_state(self) -> None:
        """
        初始化任务状态：
        - success_pairs：缓存执行结果
        """
        self.success_pairs: list[tuple[Any, Any]] = []  # task - result
        self.metrics.reset_state()

    def init_inlet(self, fail_queue: MPQueue, log_queue: MPQueue) -> None:
        """
        初始化收集器

        :param fail_queue: 失败队列
        :param log_queue: 日志队列
        """
        self.fail_queue = fail_queue or make_queue_backend("serial")()
        self.fail_inlet = FailInlet(self.fail_queue)

        self.log_queue = log_queue or make_queue_backend("serial")()
        self.log_inlet = LogInlet(self.log_queue, self.log_level)

    def init_queue(
        self,
        task_queues: TaskInQueue | None = None,
        result_queues: TaskOutQueue | None = None,
    ) -> None:
        """
        初始化队列

        :param task_queues: 任务队列列表
        :param result_queues: 结果队列列表
        :param fail_queue: 失败队列
        """
        mode = self.execution_mode

        self.task_queues = task_queues or make_task_in_queue(
            mode=mode,
            executor=self,
        )
        self.result_queues = result_queues or make_task_out_queue(
            mode=mode,
            executor=self,
        )

    def init_dispatch(self) -> None:
        """
        初始化任务运行器
        """
        self.dispatch = TaskDispatch(self, self.func, self.max_workers)

    def init_spout(self) -> None:
        """
        初始化监听器
        """
        self.fail_spout = FailSpout("executor_errors")
        self.log_spout = LogSpout()

        self.fail_spout.start()
        self.log_spout.start()

    def init_progress(self) -> None:
        """
        初始化进度条
        """
        if not self.show_progress:
            self.task_progress: TaskProgress | NullTaskProgress = NullTaskProgress()
            return

        extra_desc = (
            f"{self.execution_mode}-{self.max_workers}"
            if self.execution_mode != "serial"
            else "serial"
        )
        progress_mode = "normal" if self.execution_mode != "async" else "async"

        self.task_progress = TaskProgress(
            total_tasks=0,
            desc=f"{self.progress_desc}({extra_desc})",
            mode=progress_mode,
        )

    def set_func(self, func: Callable) -> None:
        """
        设置执行函数

        :param func: 执行函数
        """
        self.func = func
        self._func_name = func.__name__

    def set_execution_mode(self, execution_mode: str) -> None:
        """
        设置执行模式

        :param execution_mode: 执行模式，可以是 'thread'（线程）, 'process'（进程）, 'async'（异步）, 'serial'（串行）
        """
        valid_modes = ("serial", "process", "thread", "async")
        if execution_mode in valid_modes:
            self.execution_mode = execution_mode
        else:
            raise ExecutionModeError(execution_mode)

        if hasattr(self, "metrics"):
            self.metrics.set_execution_mode(execution_mode)

    def set_ctree(
        self, host: str = "127.0.0.1", http_port: int = 7777, grpc_port: int = 7778
    ) -> None:
        """
        设置CelestialTreeClient

        :param host: CelestialTreeClient host
        :param port: CelestialTreeClient port
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

    def set_log_level(self, log_level: str) -> None:
        """
        设置日志级别

        :param log_level: 日志级别
        """
        self.log_level = log_level.upper()

    def get_name(self) -> str:
        """
        获取当前节点/管理器名称

        :return: 当前节点/管理器名称
        """
        return self._name

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

    def get_class_name(self) -> str:
        """
        获取当前节点类名

        :return: 当前节点类名
        """
        return self.__class__.__name__

    def get_execution_mode_desc(self) -> str:
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

        :return: 当前节点状态快照
        包括执行器名称(name)、函数名(func_name)、类型名(class_name)、执行模式(execution_mode)
        """
        return {
            "name": self.get_name(),
            "func_name": self.get_func_name(),
            "class_name": self.get_class_name(),
            "execution_mode": self.get_execution_mode_desc(),
        }

    def get_counts(self) -> dict:
        """
        获取当前节点的计数器

        :return: 当前节点计数器
        包括任务总数(total)、成功数(success)、错误数(error)、重复数(duplicate)
        """
        return self.metrics.get_counts()

    def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
        """
        添加需要重试的异常类型

        :param exceptions: 异常类型
        """
        self.metrics.add_retry_exceptions(*exceptions)

    def put_task_queues(self, task_source: Iterable) -> None:
        """
        将任务放入任务队列

        :param task_source: 任务源（可迭代对象）
        """
        task_queues = self.task_queues

        progress_num = 0
        for task in task_source:
            input_id = self.ctree_client.emit(
                "task.input",
                payload=self.get_summary(),
            )
            envelope = TaskEnvelope.wrap(task, input_id, source="input")
            task_queues.put(envelope)
            self.metrics.add_task_count()
            self.log_inlet.task_input(
                self.get_func_name(),
                self.get_task_repr(task),
                self.get_tag(),
                input_id,
            )

            if self.metrics.get_task_count() % 100 == 0:
                self.task_progress.add_total(100)
                progress_num += 100
        self.task_progress.add_total(self.metrics.get_task_count() - progress_num)

        # 注入终止符
        termination_id = self.ctree_client.emit(
            "termination.input",
            payload=self.get_summary(),
        )
        task_queues.put(TerminationSignal(termination_id, source="input"))
        self.log_inlet.termination_input(
            self.get_func_name(),
            self.get_tag(),
            termination_id,
        )

    async def put_task_queues_async(self, task_source: Iterable) -> None:
        """
        将任务放入任务队列(async模式)

        :param task_source: 任务源（可迭代对象）
        """
        task_queues = self.task_queues

        progress_num = 0
        for task in task_source:
            input_id = self.ctree_client.emit(
                "task.input",
                payload=self.get_summary(),
            )
            envelope = TaskEnvelope.wrap(task, input_id, source="input")
            await task_queues.put_async(envelope)
            self.metrics.add_task_count()
            self.log_inlet.task_input(
                self.get_func_name(),
                self.get_task_repr(task),
                self.get_tag(),
                input_id,
            )

            if self.metrics.get_task_count() % 100 == 0:
                self.task_progress.add_total(100)
                progress_num += 100
        self.task_progress.add_total(self.metrics.get_task_count() - progress_num)

        # 注入终止符
        termination_id = self.ctree_client.emit(
            "termination.input",
            payload=self.get_summary(),
        )
        await task_queues.put_async(TerminationSignal(termination_id, source="input"))

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

    def process_result_pairs(self) -> list[tuple[Any, Any]]:
        """
        处理结果列表。可根据需要覆写

        :return: 处理后的结果列表
        """
        return self.get_success_pairs() + self.get_error_pairs()

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
            return [format_repr(arg, self.max_info) for arg in args_list]

        if len(args) <= 3:
            formatted_args = format_args_list(args)
        else:
            # 显示前两个 + ... + 最后一个
            head = format_args_list(args[:2])
            tail = format_args_list([args[-1]])
            formatted_args = head + ["..."] + tail

        return f"({', '.join(formatted_args)})"

    def get_result_repr(self, result: Any) -> str:
        """
        获取结果信息

        :param result: 任务结果
        :return: 结果信息字符串
        """
        formatted_result = format_repr(result, self.max_info)
        return f"{formatted_result}"

    def process_task_success(
        self, task_envelope: TaskEnvelope, result: Any, start_time: float
    ) -> None:
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        result_queues = self.result_queues

        result_envelope = self._prepare_result_envelope(
            task_envelope, result, start_time
        )

        result_queues.put(result_envelope)

    async def process_task_success_async(
        self, task_envelope: TaskEnvelope, result: Any, start_time: float
    ) -> None:
        """
        统一处理成功任务, 异步版本

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        result_queues = self.result_queues

        result_envelope = self._prepare_result_envelope(
            task_envelope, result, start_time
        )

        await result_queues.put_async(result_envelope)

    def _prepare_result_envelope(
        self, task_envelope: TaskEnvelope, result: Any, start_time: float
    ) -> TaskEnvelope:
        """
        准备成功任务的结果信封

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        :return: 成功任务的结果信封
        """
        self.task_progress.update(1)
        task = task_envelope.task
        task_hash = task_envelope.hash
        task_id = task_envelope.id

        processed_result = self.process_result(task, result)
        if self.enable_success_cache:
            self.success_pairs.append((task, processed_result))

        result_id = self.ctree_client.emit(
            "task.success",
            parents=[task_id],
            payload=self.get_summary(),
        )
        result_envelope = TaskEnvelope.wrap(
            processed_result,
            result_id,
            source=self.get_tag(),
        )

        self.metrics.add_success_count()
        self.metrics.pop_retry_time(task_hash)

        self.log_inlet.task_success(
            self.get_func_name(),
            self.get_task_repr(task),
            self.execution_mode,
            self.get_result_repr(result),
            time.perf_counter() - start_time,
            task_id,
            result_id,
        )
        return result_envelope

    def handle_task_error(
        self, task_envelope: TaskEnvelope, exception: Exception
    ) -> None:
        """
        统一处理异常任务

        :param task_envelope: 发生异常的任务
        :param exception: 捕获的异常
        """
        task_queues = self.task_queues

        task_hash = task_envelope.hash

        # 基于异常类型决定重试策略
        if self.metrics.is_retry_able(task_hash, exception):
            # 如果是可重试的异常，将任务重新放入队列
            retry_envelope = self._prepare_retry_envelope(task_envelope, exception)
            task_queues.put(retry_envelope)  # 只在第一个队列存放retry task
        else:
            # 如果不是可重试的异常，直接将任务标记为失败
            self._prepare_fail_envelope(task_envelope, exception)

    async def handle_task_error_async(
        self, task_envelope: TaskEnvelope, exception: Exception
    ) -> None:
        """
        统一处理任务异常, 异步版本

        :param task_envelope: 发生异常的任务
        :param exception: 捕获的异常
        """
        task_queues = self.task_queues

        task_hash = task_envelope.hash

        # 基于异常类型决定重试策略
        if self.metrics.is_retry_able(task_hash, exception):
            # 如果是可重试的异常，将任务重新放入队列
            retry_envelope = self._prepare_retry_envelope(task_envelope, exception)
            # 只在第一个队列存放retry task
            await task_queues.put_async(retry_envelope)
        else:
            # 如果不是可重试的异常，直接将任务标记为失败
            self._prepare_fail_envelope(task_envelope, exception)

    def _prepare_retry_envelope(
        self,
        task_envelope: TaskEnvelope,
        exception: Exception,
    ) -> TaskEnvelope:
        """
        准备重试任务的信封

        :param task_envelope: 发生异常的任务
        :param exception: 捕获的异常
        :return: 重试任务的信封
        """
        _, task_hash, task_id = task_envelope.unwrap()
        self.metrics.discard_processed_set(task_hash)
        new_retry_time = self.metrics.add_retry_time(task_hash)

        retry_id = self.ctree_client.emit(
            f"task.retry.{new_retry_time}",
            parents=[task_id],
            payload=self.get_summary(),
        )
        task_envelope.change_id(retry_id)

        self.log_inlet.task_retry(
            self.get_func_name(),
            self.get_task_repr(task_envelope.task),
            new_retry_time,
            exception,
            task_id,
            retry_id,
        )

        return task_envelope

    def _prepare_fail_envelope(
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
        self.task_progress.update(1)

        error_id = self.ctree_client.emit(
            "task.error",
            parents=[task_envelope.id],
            payload=self.get_summary(),
        )

        _, task_hash, task_id = task_envelope.unwrap()
        self.metrics.pop_retry_time(task_hash)
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
        self.task_progress.update(1)
        task, _, task_id = task_envelope.unwrap()

        self.metrics.add_duplicate_count()
        duplicate_id = self.ctree_client.emit(
            "task.duplicate",
            parents=[task_id],
            payload=self.get_summary(),
        )
        self.log_inlet.task_duplicate(
            self.get_func_name(),
            self.get_task_repr(task),
            task_id,
            duplicate_id,
        )

    def start(self, task_source: Iterable) -> None:
        """
        根据 start_type 的值，选择串行、并行、异步或多进程执行任务

        :param task_source: 任务迭代器或者生成器
        """
        start_time = time.perf_counter()
        self.set_nullctree()
        self.init_spout()
        self.init_progress()
        self.init_env(
            log_queue=self.log_spout.get_queue(),
            fail_queue=self.fail_spout.get_queue(),
        )

        self.put_task_queues(task_source)
        self.fail_inlet.start_executor(self.get_tag())
        self.log_inlet.start_executor(
            self.get_func_name(),
            self.metrics.get_task_count(),
            self.get_execution_mode_desc(),
        )

        try:
            # 根据模式运行对应的任务处理函数
            if self.execution_mode in ["thread", "process"]:
                self.dispatch.run_with_pool(self.execution_mode)
            elif self.execution_mode == "async":
                # don't suggest, please use start_async
                asyncio.run(self.dispatch.run_in_async())
            elif self.execution_mode == "serial":
                self.dispatch.run_in_serial()
            else:
                raise ExecutionModeError(self.execution_mode)

        finally:
            self.release_client()
            
            self.task_progress.close()
            self.log_inlet.end_executor(
                self.get_func_name(),
                self.execution_mode,
                time.perf_counter() - start_time,
                self.metrics.get_success_count(),
                self.metrics.get_error_count(),
                self.metrics.get_duplicate_count(),
            )
            self.log_spout.stop()
            self.fail_spout.stop()

    async def start_async(self, task_source: Iterable) -> None:
        """
        异步地执行任务

        :param task_source: 任务迭代器或者生成器
        """
        start_time = time.perf_counter()
        self.set_nullctree()
        self.set_execution_mode("async")
        self.init_spout()
        self.init_progress()
        self.init_env(
            log_queue=self.log_spout.get_queue(),
            fail_queue=self.fail_spout.get_queue(),
        )

        await self.put_task_queues_async(task_source)
        self.log_inlet.start_executor(
            self.get_func_name(),
            self.metrics.get_task_count(),
            self.get_execution_mode_desc(),
        )
        self.fail_inlet.start_executor(self.get_tag())

        try:
            await self.dispatch.run_in_async()

        finally:
            self.release_client()

            self.task_progress.close()
            self.log_inlet.end_executor(
                self.get_func_name(),
                self.execution_mode,
                time.perf_counter() - start_time,
                self.metrics.get_success_count(),
                self.metrics.get_error_count(),
                self.metrics.get_duplicate_count(),
            )
            self.log_spout.stop()
            self.fail_spout.stop()

    def get_success_pairs(self) -> list[tuple[Any, Any]]:
        """
        获取成功任务的列表
        """
        return self.success_pairs

    def get_error_pairs(self) -> list[tuple[Any, Exception]]:
        """
        获取出错任务的列表
        """
        return load_task_error_pairs(str(self.fail_spout.jsonl_path))

    def release_queue(self) -> None:
        """
        清理队列
        """
        self.task_queues = None
        self.result_queues = None
        self.fail_queue = None

    def release_client(self) -> None:
        self.ctree_client = None
