from __future__ import annotations

import asyncio, time
import warnings
from asyncio import Queue as AsyncQueue
from collections import defaultdict
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import Value as MPValue
from multiprocessing import Queue as MPQueue
from queue import Queue as ThreadQueue
from threading import Event, Lock

from celestialtree import (
    Client as CelestialTreeClient,
    NullClient as NullCelestialTreeClient,
)

from .task_progress import ProgressManager, NullProgress
from .task_logging import LogListener, TaskLogger
from .task_queue import TaskQueue
from .task_types import (
    SumCounter,
    TaskEnvelope,
    TerminationSignal,
    TERMINATION_SIGNAL,
)
from .task_tools import format_repr


class TaskManager:
    _name = "Manager"

    def __init__(
        self,
        func,
        execution_mode="serial",
        worker_limit=20,
        max_retries=1,
        max_info=50,
        unpack_task_args=False,
        enable_success_cache=False,
        enable_error_cache=False,
        enable_duplicate_check=True,
        progress_desc="Processing",
        show_progress=False,
    ):
        """
        初始化 TaskManager

        :param func: 可调用对象
        :param execution_mode: 执行模式，可选 'serial', 'thread', 'process', 'async'
        :param worker_limit: 同时处理数量
        :param max_retries: 任务的最大重试次数
        :param max_info: 日志中每条信息的最大长度
        :param unpack_task_args: 是否将任务参数解包
        :param enable_success_cache: 是否启用成功结果缓存, 将成功结果保存在 success_dict 中
        :param enable_error_cache: 是否启用失败结果缓存, 将失败结果保存在 error_dict 中
        :param enable_duplicate_check: 是否启用重复检查
        :param progress_desc: 进度条显示名称
        :param show_progress: 进度条显示与否
        """
        if (enable_success_cache == True or enable_error_cache == True) and enable_duplicate_check == False:
            warnings.warn(
                "Result cache is enabled while duplicate check is disabled. "
                "This may cause the number of cached results to differ from the number of input tasks "
                "due to duplicated task execution.",
                RuntimeWarning,
            )

        self.func = func
        self.execution_mode = execution_mode
        self.worker_limit = worker_limit
        self.max_retries = max_retries
        self.max_info = max_info

        self.unpack_task_args = unpack_task_args
        self.enable_success_cache = enable_success_cache
        self.enable_error_cache = enable_error_cache
        self.enable_duplicate_check = enable_duplicate_check

        self.progress_desc = progress_desc
        self.show_progress = show_progress

        self.thread_pool = None
        self.process_pool = None

        self.retry_exceptions = tuple()  # 需要重试的异常类型
        self.ctree_client = NullCelestialTreeClient()

        self.init_counter()

    def init_counter(self):
        """
        初始化计数器
        """
        self.task_counter = SumCounter()
        self.success_counter = MPValue("i", 0)
        self.error_counter = MPValue("i", 0)
        self.duplicate_counter = MPValue("i", 0)

        self.init_extra_counter()

    def init_extra_counter(self):
        """
        初始化额外计数器, 用于有特殊需要的task_node
        """
        pass

    def init_env(
        self, task_queues=None, result_queues=None, fail_queue=None, logger_queue=None
    ):
        """
        初始化环境

        :param task_queues: 任务队列列表
        :param result_queues: 结果队列列表
        :param fail_queue: 失败队列
        :param logger_queue: 日志队列
        """
        self.init_state()
        self.init_pool()
        self.init_logger(logger_queue)
        self.init_queue(task_queues, result_queues, fail_queue)

    def init_state(self):
        """
        初始化任务状态：
        - success_dict / error_dict：缓存执行结果
        - retry_time_dict：记录重试次数
        - processed_set：用于重复检测
        """
        self.success_dict = {}  # task -> result
        self.error_dict = {}  # task -> exception

        self.retry_time_dict = {}  # task_hash -> retry_time
        self.processed_set = set()  # task_hash

    def init_pool(self):
        """
        初始化线程池或进程池
        """
        # 可以复用的线程池或进程池
        if self.execution_mode == "thread" and self.thread_pool is None:
            self.thread_pool = ThreadPoolExecutor(max_workers=self.worker_limit)
        elif self.execution_mode == "process" and self.process_pool is None:
            self.process_pool = ProcessPoolExecutor(max_workers=self.worker_limit)

    def init_logger(self, logger_queue):
        """
        初始化日志器
        """
        self.logger_queue = logger_queue or ThreadQueue()
        self.task_logger = TaskLogger(self.logger_queue)

    def init_queue(self, task_queues: TaskQueue=None, result_queues: TaskQueue=None, fail_queue: TaskQueue=None):
        """
        初始化队列

        :param task_queues: 任务队列列表
        :param result_queues: 结果队列列表
        :param fail_queue: 失败队列
        :param logger_queue: 日志队列
        """
        queue_map = {
            "process": ThreadQueue,  # MPqueue
            "async": AsyncQueue,
            "thread": ThreadQueue,
            "serial": ThreadQueue,
        }

        # task_queues, result_queues与fail_queue只会在节点进程内运行, 因此如果不涉及多个进程的节点间通信, 可以全部使用ThreadQueue
        self.task_queues = task_queues or TaskQueue(
            [queue_map[self.execution_mode]()],
            [None],
            self.logger_queue,
            self.get_tag(),
            "in",
        )
        self.result_queues = result_queues or TaskQueue(
            [queue_map[self.execution_mode]()],
            [None],
            self.logger_queue,
            self.get_tag(),
            "out",
        )
        self.fail_queue: ThreadQueue | MPQueue | AsyncQueue = (
            fail_queue or queue_map[self.execution_mode]()
        )

    def init_listener(self, log_level="INFO"):
        """
        初始化监听器
        """
        self.log_listener = LogListener(log_level)
        self.log_listener.start()

    def init_progress(self):
        """
        初始化进度条
        """
        if not self.show_progress:
            self.progress_manager = NullProgress()
            return

        extra_desc = (
            f"{self.execution_mode}-{self.worker_limit}"
            if self.execution_mode != "serial"
            else "serial"
        )
        progress_mode = "normal" if self.execution_mode != "async" else "async"

        self.progress_manager = ProgressManager(
            total_tasks=0,
            desc=f"{self.progress_desc}({extra_desc})",
            mode=progress_mode,
        )

    def set_execution_mode(self, execution_mode):
        """
        设置执行模式

        :param execution_mode: 执行模式，可以是 'thread'（线程）, 'process'（进程）, 'async'（异步）, 'serial'（串行）
        """
        self.execution_mode = (
            execution_mode
            if execution_mode in ["thread", "process", "async", "serial"]
            else "serial"
        )

    def set_ctree(self, host="127.0.0.1", port=7777):
        """
        设置CelestialTreeClient

        :param host: CelestialTreeClient host
        :param port: CelestialTreeClient port
        """
        self.ctree_client = CelestialTreeClient(host=host, port=port)
        if not self.ctree_client.health():
            self.ctree_client = NullCelestialTreeClient()

    def set_nullctree(self, event_id=None):
        """
        设置NullCelestialTreeClient

        :param event_id: 事件ID
        :param event_lock: 事件锁
        """
        self.ctree_client = NullCelestialTreeClient(event_id)

    def reset_counter(self):
        """
        重置计数器
        """
        self.task_counter.reset()
        self.success_counter.value = 0
        self.error_counter.value = 0
        self.duplicate_counter.value = 0

        self.reset_extra_counter()

    def reset_extra_counter(self):
        """
        重置额外计数器, 用于有特殊需要的task_node
        """
        pass

    def get_func_name(self) -> str:
        """
        获取当前节点函数名

        :return: 当前节点函数名
        """
        return self.func.__name__

    def get_tag(self) -> str:
        """
        获取当前节点/管理器标签

        :return: 当前节点/管理器标签
        """
        if hasattr(self, "_tag"):
            return self._tag
        self._tag = f"{self._name}[{self.func.__name__}]"
        return self._tag

    def get_execution_mode_desc(self) -> str:
        """
        获取当前节点执行模式

        :return: 当前节点执行模式
        """
        return (
            self.execution_mode
            if self.execution_mode == "serial"
            else f"{self.execution_mode}-{self.worker_limit}"
        )

    def add_retry_exceptions(self, *exceptions):
        """
        添加需要重试的异常类型

        :param exceptions: 异常类型
        """
        self.retry_exceptions = self.retry_exceptions + tuple(exceptions)

    def put_task_queues(self, task_source):
        """
        将任务放入任务队列

        :param task_source: 任务源（可迭代对象）
        """
        progress_num = 0
        for task in task_source:
            input_id = self.ctree_client.emit(
                "task.input", message=f"In '{self.get_tag()}'"
            )
            envelope = TaskEnvelope.wrap(task, input_id)
            self.task_queues.put_first(envelope)
            self.update_task_counter()
            self.task_logger.task_input(
                self.get_func_name(),
                self.get_task_repr(task),
                self.get_tag(),
                input_id,
            )

            if self.task_counter.value % 100 == 0:
                self.progress_manager.add_total(100)
                progress_num += 100
        self.progress_manager.add_total(self.task_counter.value - progress_num)

    async def put_task_queues_async(self, task_source):
        """
        将任务放入任务队列(async模式)

        :param task_source: 任务源（可迭代对象）
        """
        progress_num = 0
        for task in task_source:
            input_id = self.ctree_client.emit(
                "task.input", message=f"In '{self.get_tag()}'"
            )
            envelope = TaskEnvelope.wrap(task, input_id)
            await self.task_queues.put_first_async(envelope)
            self.update_task_counter()
            self.task_logger.task_input(
                self.get_func_name(),
                self.get_task_repr(task),
                self.get_tag(),
                input_id,
            )

            if self.task_counter.value % 100 == 0:
                self.progress_manager.add_total(100)
                progress_num += 100
        self.progress_manager.add_total(self.task_counter.value - progress_num)

    def put_fail_queue(self, task, error, error_id):
        """
        将失败的任务放入失败队列

        :param task: 失败的任务
        :param error: 任务失败的异常
        """
        self.fail_queue.put(
            {
                "ts": time.time(),
                "task": str(task),
                "error_info": f"{type(error).__name__}({error})",
                "error_id": error_id,
            }
        )

    async def put_fail_queue_async(self, task, error, error_id):
        """
        将失败的任务放入失败队列（异步版本）

        :param task: 失败的任务
        :param error: 任务失败的异常
        """
        await self.fail_queue.put(
            {
                "ts": time.time(),
                "task": str(task),
                "error_info": f"{type(error).__name__}({error})",
                "error_id": error_id,
            }
        )

    def update_task_counter(self):
        # 加锁方式（保证正确）
        self.task_counter.add_init_value(1)

    def update_success_counter(self):
        # 加锁方式（保证正确）
        with self.success_counter.get_lock():
            self.success_counter.value += 1

    async def update_success_counter_async(self):
        await asyncio.to_thread(self.update_success_counter)

    def update_error_counter(self):
        # 加锁方式（保证正确）
        with self.error_counter.get_lock():
            self.error_counter.value += 1

    def update_duplicate_counter(self):
        # 加锁方式（保证正确）
        with self.duplicate_counter.get_lock():
            self.duplicate_counter.value += 1

    def is_tasks_finished(self) -> bool:
        """
        判断任务是否完成
        """
        processed = (
            self.success_counter.value
            + self.error_counter.value
            + self.duplicate_counter.value
        )
        return self.task_counter.value == processed

    def is_duplicate(self, task_hash):
        """
        判断任务是否重复
        """
        # 我认为只要在add_processed_set中控制processed_set的流入就可以了
        # 但gpt强烈建议我加上
        if not self.enable_duplicate_check:
            return False
        return task_hash in self.processed_set

    def add_processed_set(self, task_hash):
        """
        将任务ID添加到已处理集合中

        :param task_hash: 任务hash
        """
        if self.enable_duplicate_check:
            self.processed_set.add(task_hash)

    def get_args(self, task):
        """
        从 obj 中获取参数。可根据需要覆写

        在这个示例中，我们根据 unpack_task_args 决定是否解包参数
        """
        if self.unpack_task_args:
            return task
        return (task,)

    def process_result(self, task, result):
        """
        从结果队列中获取结果，并进行处理。可根据需要覆写

        在这个示例中，我们只是简单地返回结果
        """
        return result

    def process_result_dict(self):
        """
        处理结果字典。可根据需要覆写

        在这个示例中，我们合并了字典并返回
        """
        return {**self.success_dict, **self.error_dict}

    def handle_error_dict(self):
        """
        处理错误字典。可根据需要覆写

        在这个示例中，我们将列表合并为错误组
        """
        error_groups = defaultdict(list)
        for task, error in self.error_dict.items():
            error_groups[error].append(task)

        return dict(error_groups)  # 转换回普通字典

    def get_task_repr(self, task) -> str:
        """
        获取任务参数信息的可读字符串表示

        :param task: 任务对象
        :return: 任务参数信息字符串
        """
        args = self.get_args(task)

        # 格式化每个参数
        def format_args_list(args_list):
            return [format_repr(arg, self.max_info) for arg in args_list]

        if len(args) <= 3:
            formatted_args = format_args_list(args)
        else:
            # 显示前两个 + ... + 最后一个
            head = format_args_list(args[:2])
            tail = format_args_list([args[-1]])
            formatted_args = head + ["..."] + tail

        return f"({', '.join(formatted_args)})"

    def get_result_repr(self, result):
        """
        获取结果信息

        :param result: 任务结果
        :return: 结果信息字符串
        """
        formatted_result = format_repr(result, self.max_info)
        return f"{formatted_result}"

    def process_task_success(self, task_envelope: TaskEnvelope, result, start_time):
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        task = task_envelope.task
        task_hash = task_envelope.hash
        task_id = task_envelope.id

        processed_result = self.process_result(task, result)
        if self.enable_success_cache:
            self.success_dict[task] = processed_result

        result_id = self.ctree_client.emit(
            "task.success", parents=[task_id], message=f"In '{self.get_tag()}'"
        )
        result_envelope = TaskEnvelope.wrap(processed_result, result_id)

        # 清理 retry_time_dict
        self.retry_time_dict.pop(task_hash, None)

        self.update_success_counter()
        self.result_queues.put(result_envelope)
        self.task_logger.task_success(
            self.get_func_name(),
            self.get_task_repr(task),
            self.execution_mode,
            self.get_result_repr(result),
            time.time() - start_time,
            task_id,
            result_id,
        )

    async def process_task_success_async(
        self, task_envelope: TaskEnvelope, result, start_time
    ):
        """
        统一处理成功任务, 异步版本

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        task = task_envelope.task
        task_hash = task_envelope.hash
        task_id = task_envelope.id

        processed_result = self.process_result(task, result)
        if self.enable_success_cache:
            self.success_dict[task] = processed_result

        result_id = self.ctree_client.emit(
            "task.success", parents=[task_id], message=f"In '{self.get_tag()}'"
        )
        result_envelope = TaskEnvelope.wrap(processed_result, result_id)

        # 清理 retry_time_dict
        self.retry_time_dict.pop(task_hash, None)

        await self.update_success_counter_async()
        await self.result_queues.put_async(result_envelope)
        self.task_logger.task_success(
            self.get_func_name(),
            self.get_task_repr(task),
            self.execution_mode,
            self.get_result_repr(result),
            time.time() - start_time,
            task_id,
            result_id,
        )

    def handle_task_error(self, task_envelope: TaskEnvelope, exception: Exception):
        """
        统一处理异常任务

        :param task_envelope: 发生异常的任务
        :param exception: 捕获的异常
        :return 是否需要重试
        """
        task = task_envelope.task
        task_hash = task_envelope.hash
        task_id = task_envelope.id

        retry_time = self.retry_time_dict.setdefault(task_hash, 0)

        # 基于异常类型决定重试策略
        if (
            isinstance(exception, self.retry_exceptions)
            and retry_time < self.max_retries
        ):
            self.progress_manager.add_total(1)
            self.processed_set.discard(task_hash)
            self.retry_time_dict[task_hash] += 1

            retry_id = self.ctree_client.emit(
                f"task.retry.{retry_time+1}",
                parents=[task_id],
                message=f"In '{self.get_tag()}'",
            )
            task_envelope.change_id(retry_id)
            self.task_queues.put_first(task_envelope)  # 只在第一个队列存放retry task

            self.task_logger.task_retry(
                self.get_func_name(),
                self.get_task_repr(task),
                self.retry_time_dict[task_hash],
                exception,
                task_id,
                retry_id,
            )
        else:
            # 如果不是可重试的异常，直接将任务标记为失败
            if self.enable_error_cache:
                self.error_dict[task] = exception

            error_id = self.ctree_client.emit(
                "task.error", parents=[task_id], message=f"In '{self.get_tag()}'"
            )

            # 清理 retry_time_dict
            self.retry_time_dict.pop(task_hash, None)

            self.update_error_counter()
            self.put_fail_queue(task, exception, error_id)
            self.task_logger.task_error(
                self.get_func_name(),
                self.get_task_repr(task),
                exception,
                task_id,
                error_id,
            )

    async def handle_task_error_async(
        self, task_envelope: TaskEnvelope, exception: Exception
    ):
        """
        统一处理任务异常, 异步版本

        :param task_envelope: 发生异常的任务
        :param exception: 捕获的异常
        :return 是否需要重试
        """
        task = task_envelope.task
        task_hash = task_envelope.hash
        task_id = task_envelope.id

        retry_time = self.retry_time_dict.setdefault(task_hash, 0)

        # 基于异常类型决定重试策略
        if (
            isinstance(exception, self.retry_exceptions)
            and retry_time < self.max_retries
        ):
            self.progress_manager.add_total(1)
            self.processed_set.discard(task_hash)
            self.retry_time_dict[task_hash] += 1

            retry_id = self.ctree_client.emit(
                f"task.retry.{retry_time+1}",
                parents=[task_id],
                message=f"In '{self.get_tag()}'",
            )
            task_envelope.change_id(retry_id)
            await self.task_queues.put_first_async(
                task_envelope
            )  # 只在第一个队列存放retry task

            self.task_logger.task_retry(
                self.get_func_name(),
                self.get_task_repr(task),
                self.retry_time_dict[task_hash],
                exception,
                task_id,
                retry_id,
            )
        else:
            # 如果不是可重试的异常，直接将任务标记为失败
            if self.enable_error_cache:
                self.error_dict[task] = exception

            error_id = self.ctree_client.emit(
                "task.error", parents=[task_id], message=f"In '{self.get_tag()}'"
            )

            # 清理 retry_time_dict
            self.retry_time_dict.pop(task_hash, None)

            self.update_error_counter()
            await self.put_fail_queue_async(task, exception, error_id)
            self.task_logger.task_error(
                self.get_func_name(),
                self.get_task_repr(task),
                exception,
                task_id,
                error_id,
            )

    def deal_dupliacte(self, task_envelope: TaskEnvelope):
        """
        处理重复任务
        """
        task = task_envelope.task
        task_id = task_envelope.id

        self.update_duplicate_counter()
        duplicate_id = self.ctree_client.emit(
            "task.duplicate",
            parents=[task_envelope.id],
            message=f"In '{self.get_tag()}'",
        )
        self.task_logger.task_duplicate(
            self.get_func_name(),
            self.get_task_repr(task),
            task_id,
            duplicate_id,
        )

    def start(self, task_source: Iterable):
        """
        根据 start_type 的值，选择串行、并行、异步或多进程执行任务

        :param task_source: 任务迭代器或者生成器
        """
        start_time = time.time()
        self.init_listener()
        self.init_progress()
        self.init_env(logger_queue=self.log_listener.get_queue())

        self.put_task_queues(task_source)
        self.task_queues.put(TERMINATION_SIGNAL)
        self.task_logger.start_manager(
            self.get_func_name(),
            self.task_counter.value,
            self.get_execution_mode_desc(),
        )

        try:
            # 根据模式运行对应的任务处理函数
            if self.execution_mode == "thread":
                self.run_with_executor(self.thread_pool)
            elif self.execution_mode == "process":
                self.run_with_executor(self.process_pool)
                # cleanup_mpqueue(self.task_queues)
            elif self.execution_mode == "async":
                # don't suggest, please use start_async
                asyncio.run(self.run_in_async())
            else:
                self.set_execution_mode("serial")
                self.run_in_serial()

        finally:
            self.release_pool()
            self.progress_manager.close()

            self.task_logger.end_manager(
                self.get_func_name(),
                self.execution_mode,
                time.time() - start_time,
                self.success_counter.value,
                self.error_counter.value,
                self.duplicate_counter.value,
            )
            self.log_listener.stop()

    async def start_async(self, task_source: Iterable):
        """
        异步地执行任务

        :param task_source: 任务迭代器或者生成器
        """
        start_time = time.time()
        self.set_execution_mode("async")
        self.init_listener()
        self.init_progress()
        self.init_env(logger_queue=self.log_listener.get_queue())

        await self.put_task_queues_async(task_source)
        await self.task_queues.put_async(TERMINATION_SIGNAL)
        self.task_logger.start_manager(
            self.get_func_name(),
            self.task_counter.value,
            self.get_execution_mode_desc(),
        )

        try:
            await self.run_in_async()

        finally:
            self.release_pool()
            self.progress_manager.close()

            self.task_logger.end_manager(
                self.get_func_name(),
                self.execution_mode,
                time.time() - start_time,
                self.success_counter.value,
                self.error_counter.value,
                self.duplicate_counter.value,
            )
            self.log_listener.stop()

    def run_in_serial(self):
        """
        串行地执行任务
        """
        # 从队列中依次获取任务并执行
        while True:
            envelope = self.task_queues.get()
            if isinstance(envelope, TerminationSignal):
                break

            task = envelope.task
            task_hash = envelope.hash

            if self.is_duplicate(task_hash):
                self.deal_dupliacte(envelope)
                self.progress_manager.update(1)
                continue
            self.add_processed_set(task_hash)
            try:
                start_time = time.time()
                result = self.func(*self.get_args(task))
                self.process_task_success(envelope, result, start_time)
            except Exception as error:
                self.handle_task_error(envelope, error)
            self.progress_manager.update(1)

        self.task_queues.reset()

        if not self.is_tasks_finished():
            self.task_logger._log("DEBUG", f"{self.get_func_name()} is not finished.")
            self.task_queues.put(TERMINATION_SIGNAL)
            self.run_in_serial()

    def run_with_executor(self, executor: ThreadPoolExecutor | ProcessPoolExecutor):
        """
        使用指定的执行池（线程池或进程池）来并行执行任务。

        :param executor: 线程池或进程池
        """
        task_start_dict = {}  # 用于存储任务开始时间

        # 用于追踪进行中任务数的计数器和事件
        in_flight = 0
        in_flight_lock = Lock()
        all_done_event = Event()
        all_done_event.set()  # 初始为无任务状态，设为完成状态

        def on_task_done(
            future, envelope: TaskEnvelope, progress_manager: ProgressManager
        ):
            # 回调函数中处理任务结果
            progress_manager.update(1)
            task_id = envelope.id

            try:
                result = future.result()
                start_time = task_start_dict.pop(task_id, None)
                self.process_task_success(envelope, result, start_time)
            except Exception as error:
                task_start_dict.pop(task_id, None)
                self.handle_task_error(envelope, error)
            # 任务完成后减少in_flight计数
            with in_flight_lock:
                nonlocal in_flight
                in_flight -= 1
                if in_flight == 0:
                    all_done_event.set()

        # 从任务队列中提交任务到执行池
        while True:
            envelope = self.task_queues.get()
            if isinstance(envelope, TerminationSignal):
                break

            task = envelope.task
            task_hash = envelope.hash
            task_id = envelope.id

            if isinstance(task, TerminationSignal):
                # 收到终止信号后不再提交新任务
                break
            elif self.is_duplicate(task_hash):
                self.deal_dupliacte(envelope)
                self.progress_manager.update(1)
                continue
            self.add_processed_set(task_hash)

            # 提交新任务时增加in_flight计数，并清除完成事件
            with in_flight_lock:
                in_flight += 1
                all_done_event.clear()

            task_start_dict[task_id] = time.time()
            future = executor.submit(self.func, *self.get_args(task))
            future.add_done_callback(
                lambda f, t_e=envelope: on_task_done(f, t_e, self.progress_manager)
            )

        # 等待所有已提交任务完成（包括回调）
        all_done_event.wait()

        # 所有任务和回调都完成了，现在可以安全关闭进度条
        self.task_queues.reset()

        if not self.is_tasks_finished():
            self.task_logger._log("DEBUG", f"{self.get_func_name()} is not finished.")
            self.task_queues.put(TERMINATION_SIGNAL)
            self.run_with_executor(executor)

    async def run_in_async(self):
        """
        异步地执行任务，限制并发数量
        """
        semaphore = asyncio.Semaphore(self.worker_limit)  # 限制并发数量

        async def sem_task(envelope: TaskEnvelope):
            start_time = time.time()  # 记录任务开始时间
            async with semaphore:  # 使用信号量限制并发
                result = await self._run_single_task(envelope.task)
                return envelope, result, start_time  # 返回 task, result 和 start_time

        # 创建异步任务列表
        async_tasks = []

        while True:
            envelope = await self.task_queues.get_async()
            if isinstance(envelope, TerminationSignal):
                break

            task = envelope.task
            task_hash = envelope.hash

            if self.is_duplicate(task_hash):
                self.deal_dupliacte(envelope)
                self.progress_manager.update(1)
                continue
            self.add_processed_set(task_hash)
            async_tasks.append(sem_task(envelope))  # 使用信号量包裹的任务

        # 并发运行所有任务
        for envelope, result, start_time in await asyncio.gather(
            *async_tasks, return_exceptions=True
        ):
            if not isinstance(result, Exception):
                await self.process_task_success_async(envelope, result, start_time)
            else:
                await self.handle_task_error_async(envelope, result)
            self.progress_manager.update(1)

        self.task_queues.reset()

        if not self.is_tasks_finished():
            self.task_logger._log("DEBUG", f"{self.get_func_name()} is not finished.")
            await self.task_queues.put_async(TERMINATION_SIGNAL)
            await self.run_in_async()

    async def _run_single_task(self, task):
        """
        运行单个任务并捕获异常
        """
        try:
            result = await self.func(*self.get_args(task))
            return result
        except Exception as error:
            return error

    def get_success_dict(self) -> dict:
        """
        获取成功任务的字典
        """
        return dict(self.success_dict)

    def get_error_dict(self) -> dict:
        """
        获取出错任务的字典
        """
        return dict(self.error_dict)

    def release_queue(self):
        """
        清理环境
        """
        self.task_queues = None
        self.result_queues = None
        self.fail_queue = None

    def release_pool(self):
        """
        关闭线程池和进程池，释放资源
        """
        for pool in [self.thread_pool, self.process_pool]:
            if pool:
                pool.shutdown(wait=True)
        self.thread_pool = None
        self.process_pool = None

    def test_method(self, execution_mode: str, task_list: list) -> float:
        """
        测试方法
        """
        start = time.time()
        self.set_execution_mode(execution_mode)
        self.init_counter()
        self.init_state()
        self.start(task_list)
        return time.time() - start

    def test_methods(self, task_source: Iterable, execution_modes: list = None) -> list:
        """
        测试多种方法
        """
        # 如果 task_source 是生成器或一次性可迭代对象，需要提前转化成列表
        # 确保对不同模式的测试使用同一批任务数据
        task_list = list(task_source)
        execution_modes = execution_modes or ["serial", "thread", "process"]

        results = []
        for mode in execution_modes:
            result = self.test_method(mode, task_list)
            results.append([result])
        return results, execution_modes, ["Time"]

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release_queue()
