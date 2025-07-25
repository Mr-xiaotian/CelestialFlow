from __future__ import annotations

import asyncio, time
from asyncio import Queue as AsyncQueue, QueueEmpty
from collections import defaultdict
from collections.abc import Iterable  
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import Queue as MPQueue
from queue import Queue as ThreadQueue, Empty
from threading import Event, Lock
from typing import List

from httpx import (
    ConnectError,
    ConnectTimeout,
    PoolTimeout,
    ProtocolError,
    ReadError,
    ReadTimeout,
    ProxyError,
    RequestError,
)

from .task_progress import ProgressManager
from .task_support import TERMINATION_SIGNAL, TerminationSignal, LogListener, TaskLogger, ValueWrapper, null_lock
from .task_tools import are_queues_empty, are_queues_empty_async, make_hashable, format_repr, object_to_str_hash


class TaskManager:
    def __init__(
        self,
        func,
        execution_mode="serial",
        worker_limit=50,
        max_retries=3,
        max_info=50,
        unpack_task_args=False,
        enable_result_cache=False,
        progress_desc="Processing",
        show_progress=False,
    ):
        """
        初始化 TaskManager

        :param func: 可调用对象
        :param execution_mode: 执行模式，可选 'serial', 'thread', 'process', 'async'
        :param worker_limit: 同时处理数量
        :param max_retries: 任务的最大重试次数
        :param progress_desc: 进度条显示名称
        :param show_progress: 进度条显示与否
        """
        self.func = func
        self.execution_mode = execution_mode
        self.worker_limit = worker_limit
        self.max_retries = max_retries
        self.max_info = max_info
        self.unpack_task_args = unpack_task_args
        self.enable_result_cache = enable_result_cache

        self.progress_desc = progress_desc
        self.show_progress = show_progress

        self.thread_pool = None
        self.process_pool = None

        self.current_index = 0  # 记录起始队列索引
        self.terminated_queue_set = set()

        self.prev_stages: List[TaskManager] = []
        self.set_stage_name(None)

        self.retry_exceptions = (
            ConnectTimeout,
            ProtocolError,
            ReadError,
            ConnectError,
            PoolTimeout,
            ReadTimeout,
            ProxyError,
        )  # 需要重试的异常类型

        self.init_counter()

    def init_counter(self, success_counter=None, error_counter=None, duplicate_counter=None, counter_lock=None, extra_stats=None):
        """
        初始化计数器
        """
        self.success_counter = success_counter if success_counter is not None else ValueWrapper()
        self.error_counter = error_counter if error_counter is not None else ValueWrapper()
        self.duplicate_counter = duplicate_counter if duplicate_counter is not None else ValueWrapper()
        self.counter_lock = counter_lock if counter_lock is not None else null_lock

        self.extra_stats = extra_stats if extra_stats is not None else {}

    def init_env(self, task_queues=None, result_queues=None, fail_queue=None, logger_queue=None):
        """
        初始化环境
        """
        self.init_queue(task_queues, result_queues, fail_queue, logger_queue)
        self.init_state()
        self.init_pool()
        self.init_logger()

    def init_queue(self, task_queues=None, result_queues=None, fail_queue=None, logger_queue=None):
        """
        初始化队列
        """
        queue_map = {
            "process": ThreadQueue, #MPqueue
            "async": AsyncQueue,
            "thread": ThreadQueue,
            "serial": ThreadQueue,
        }

        # task_queues, result_queues与fail_queue只会在节点进程内运行, 因此如果不涉及多个进程的节点间通信, 可以全部使用ThreadQueue
        self.task_queues: List[ThreadQueue|MPQueue|AsyncQueue]   = task_queues or [queue_map[self.execution_mode]()]
        self.result_queues: List[ThreadQueue|MPQueue|AsyncQueue] = result_queues or [queue_map[self.execution_mode]()]
        self.fail_queue: ThreadQueue|MPQueue|AsyncQueue          = fail_queue or queue_map[self.execution_mode]()
        self.logger_queue: ThreadQueue|MPQueue                   = logger_queue or ThreadQueue()

    def init_state(self):
        """
        初始化任务状态：
        - success_dict / error_dict：缓存执行结果
        - retry_time_dict：记录重试次数
        - processed_set：用于重复检测
        """
        self.success_dict = {}
        self.error_dict = {}
        self.retry_time_dict = {} # task_id -> retry_time

        self.processed_set = set()

    def init_pool(self):
        """
        初始化线程池或进程池
        """
        # 可以复用的线程池或进程池
        if self.execution_mode == "thread" and self.thread_pool is None:
            self.thread_pool = ThreadPoolExecutor(max_workers=self.worker_limit)
        elif self.execution_mode == "process" and self.process_pool is None:
            self.process_pool = ProcessPoolExecutor(max_workers=self.worker_limit)

    def init_logger(self):
        """
        初始化日志
        """
        self.task_logger = TaskLogger(self.logger_queue)

    def init_listener(self):
        """
        初始化监听器
        """
        self.log_listener = LogListener("INFO")
        self.log_listener.start()

    def init_progress(self):
        """
        初始化进度条
        """
        extra_desc = f"{self.execution_mode}-{self.worker_limit}" if self.execution_mode != "serial" else "serial"
        progress_mode = "normal" if self.execution_mode != "async" else "async"

        self.progress_manager = ProgressManager(
            total_tasks=0,
            desc=f"{self.progress_desc}({extra_desc})",
            mode=progress_mode,
            show_progress=self.show_progress,
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

    def set_graph_context(
        self,
        next_stages: List[TaskManager] = None,
        stage_mode: str = None,
        stage_name: str = None,
    ):
        """
        设置链式上下文(仅限组成graph时)
        :param next_stages: 后续节点列表
        :param stage_mode: 当前节点执行模式, 可以是 'serial'（串行）或 'process'（并行）
        :param name: 当前节点名称
        """
        self.set_next_stages(next_stages)
        self.set_stage_mode(stage_mode)
        self.set_stage_name(stage_name)

    def set_next_stages(self, next_stages: List[TaskManager]):
        """
        设置后续节点列表, 并为后续节点添加本节点为前置节点
        """
        self.next_stages = next_stages or []  # 默认为空列表
        for next_stage in self.next_stages:
            next_stage.add_prev_stages(self)

    def set_stage_mode(self, stage_mode: str):
        """
        设置当前节点在graph中的执行模式, 可以是 'serial'（串行）或 'process'（并行）
        """
        self.stage_mode = stage_mode if stage_mode == "process" else "serial"

    def set_stage_name(self, name: str):
        """
        设置当前节点名称
        """
        self.stage_name = name or id(self)

    def add_prev_stages(self, prev_stage: TaskManager):
        """
        添加前置节点
        """
        self.prev_stages.append(prev_stage)

    def get_stage_tag(self):
        """
        获取当前节点在graph中的标签
        """
        return f"{self.stage_name}[{self.func.__name__}]"
    
    def get_stage_summary(self) -> dict:
        """
        获取当前节点的状态快照
        """
        return {
            "stage_mode": self.stage_mode,
            "execution_mode": self.execution_mode if self.execution_mode == "serial" else self.execution_mode + f"-{self.worker_limit}",
            "func_name": self.func.__name__,
            "class_name": self.__class__.__name__,
        }

    def add_retry_exceptions(self, *exceptions):
        """
        添加需要重试的异常类型
        """
        self.retry_exceptions = self.retry_exceptions + tuple(exceptions)

    def get_task_queues(self, poll_interval: float = 0.01):
        """
        从多个队列中轮询获取任务。

        :param poll_interval: 每轮遍历后的等待时间（秒）
        :return: 获取到的任务，或 TerminationSignal 表示所有队列已终止
        """
        total_queues = len(self.task_queues)

        if total_queues == 1:
            # ✅ 只有一个队列时，使用阻塞式 get，提高效率
            queue = self.task_queues[0]
            item = queue.get()  # 阻塞等待，无需 sleep
            if isinstance(item, TerminationSignal):
                self.terminated_queue_set.add(0)
                self.task_logger._log("TRACE", f"get_task_queues: queue[0] terminated")
                return TERMINATION_SIGNAL
            return item

        while True:
            for i in range(total_queues):
                idx = (self.current_index + i) % total_queues  # 轮转访问
                if idx in self.terminated_queue_set:
                    continue
                queue = self.task_queues[idx]
                try:
                    item = queue.get_nowait()
                    if isinstance(item, TerminationSignal):
                        self.terminated_queue_set.add(idx)
                        self.task_logger._log("TRACE", f"get_task_queues: queue[{idx}] terminated")
                        continue
                    self.current_index = (idx + 1) % total_queues  # 下一轮从下一个队列开始
                    return item
                except Empty:
                    continue
                except Exception as e:
                    self.task_logger._log("WARNING", f"get_task_queues: Error from queue[{idx}]: {type(e).__name__}({e})")
                    continue

            # 所有队列都终止了
            if len(self.terminated_queue_set) == total_queues:
                return TERMINATION_SIGNAL

            # 所有队列都暂时无数据，避免 busy-wait
            time.sleep(poll_interval)

    async def get_task_queues_async(self, poll_interval=0.01):
        """
        异步轮询多个 AsyncQueue，获取任务。

        :param poll_interval: 全部为空时的 sleep 间隔（秒）
        :return: task 或 TerminationSignal
        """
        total_queues = len(self.task_queues)

        if total_queues == 1:
            # ✅ 单队列直接 await 阻塞等待
            queue = self.task_queues[0]
            task = await queue.get()
            if isinstance(task, TerminationSignal):
                self.terminated_queue_set.add(0)
                self.task_logger._log("TRACE", "get_task_queues_async: queue[0] terminated")
                return TERMINATION_SIGNAL
            return task

        while True:
            for i in range(total_queues):
                idx = (self.current_index + i) % total_queues
                if idx in self.terminated_queue_set:
                    continue
                queue = self.task_queues[idx]
                try:
                    task = queue.get_nowait()
                    if isinstance(task, TerminationSignal):
                        self.terminated_queue_set.add(idx)
                        self.task_logger._log("TRACE", f"get_task_queues_async: queue[{idx}] terminated")
                        continue
                    self.current_index = (idx + 1) % total_queues
                    return task
                except QueueEmpty:
                    continue
                except Exception as e:
                    self.task_logger._log("WARNING", f"get_task_queues_async: queue[{idx}] error: {type(e).__name__}({e})")
                    continue

            if len(self.terminated_queue_set) == total_queues:
                return TERMINATION_SIGNAL

            await asyncio.sleep(poll_interval)

    def put_task_queues(self, task_source) -> int:
        """
        将任务放入任务队列
        """
        task_num = 0
        for item in task_source:
            self.task_queues[0].put(make_hashable(item))
            task_num += 1
        self.progress_manager.add_total(task_num)
        return task_num

    async def put_task_queues_async(self, task_source) -> int:
        """
        将任务放入任务队列(async模式)
        """
        task_num = 0
        for item in task_source:
            await self.task_queues[0].put(make_hashable(item))
            task_num += 1
        self.progress_manager.add_total(task_num)
        return task_num

    def terminate_task_queues(self):
        """
        终止所有任务队列
        """
        for queue in self.task_queues:
            queue.put(TERMINATION_SIGNAL)  # 添加一个哨兵任务，用于结束任务队列
    
    async def terminate_task_queues_async(self):
        """
        终止所有任务队列(async模式)
        """
        for queue in self.task_queues:
            await queue.put(TERMINATION_SIGNAL)  # 添加一个哨兵任务，用于结束任务队列

    def put_result_queues(self, result):
        """
        将结果放入所有结果队列
        """
        for result_queue in self.result_queues:
            result_queue.put(result)

    async def put_result_queues_async(self, result):
        """
        将结果放入所有结果队列(async模式)
        """
        for queue in self.result_queues:
            await queue.put(result)

    def put_fail_queue(self, task, error):
        """
        将失败的任务放入失败队列
        """
        self.fail_queue.put({
            "stage_tag": self.get_stage_tag(),
            "task": str(task),
            "error_info": f"{type(error).__name__}({error})",
            "timestamp": time.time()
        })

    async def put_fail_queue_async(self, task, error):
        """
        将失败的任务放入失败队列（异步版本）
        """
        await self.fail_queue.put({
            "stage_tag": self.get_stage_tag(),
            "task": str(task),
            "error_info": f"{type(error).__name__}({error})",
            "timestamp": time.time()
        })

    def update_success_counter(self):
        # 加锁方式（保证正确）
        with self.counter_lock:
            self.success_counter.value += 1

    async def update_success_counter_async(self):
        await asyncio.to_thread(self.update_success_counter)

    def update_error_counter(self):
        # 加锁方式（保证正确）
        with self.counter_lock:
            self.error_counter.value += 1

    def update_duplicate_counter(self):
        # 加锁方式（保证正确）
        with self.counter_lock:
            self.duplicate_counter.value += 1

    def is_duplicate(self, task_id):
        """
        判断任务是否重复
        """
        return task_id in self.processed_set
    
    def deal_dupliacte(self, task):
        """
        处理重复任务
        """
        self.update_duplicate_counter()
        self.task_logger.task_duplicate(self.func.__name__, self.get_task_info(task))

    def get_args(self, task):
        """
        从 obj 中获取参数

        在这个示例中，我们假设 obj 是一个参数，并将其打包为元组返回
        """
        if self.unpack_task_args and isinstance(task, tuple):
            return task
        return (task,)

    def process_result(self, task, result):
        """
        从结果队列中获取结果，并进行处理

        在这个示例中，我们只是简单地返回结果
        """
        return result

    def process_result_dict(self):
        """
        处理结果字典

        在这个示例中，我们合并了字典并返回
        """
        success_dict = self.get_success_dict()
        error_dict = self.get_error_dict()

        return {**success_dict, **error_dict}

    def handle_error_dict(self):
        """
        处理错误字典

        在这个示例中，我们将列表合并为错误组
        """
        error_dict = self.get_error_dict()

        error_groups = defaultdict(list)
        for task, error in error_dict.items():
            error_groups[error].append(task)

        return dict(error_groups)  # 转换回普通字典
    
    def get_task_id(self, task):
        """
        获取任务ID
        """
        return object_to_str_hash(task)

    def get_task_info(self, task):
        """
        获取任务参数信息的可读字符串表示。
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

    def get_result_info(self, result):
        """
        获取结果信息
        """
        return format_repr(result, self.max_info)

    def process_task_success(self, task, result, start_time):
        """
        统一处理成功任务

        :param task: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        processed_result = self.process_result(task, result)

        if self.enable_result_cache:
            self.success_dict[task] = processed_result

        # ✅ 清理 retry_time_dict
        task_id = self.get_task_id(task)
        self.retry_time_dict.pop(task_id, None)

        self.update_success_counter()
        self.put_result_queues(processed_result)
        self.task_logger.task_success(
            self.func.__name__,
            self.get_task_info(task),
            self.execution_mode,
            self.get_result_info(result),
            time.time() - start_time,
        )

    async def process_task_success_async(self, task, result, start_time):
        """
        异步版本：统一处理成功任务

        :param task: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        processed_result = self.process_result(task, result)

        if self.enable_result_cache:
            self.success_dict[task] = processed_result

        # ✅ 清理 retry_time_dict
        task_id = self.get_task_id(task)
        self.retry_time_dict.pop(task_id, None)

        await self.update_success_counter_async()
        await self.put_result_queues_async(processed_result)
        self.task_logger.task_success(
            self.func.__name__,
            self.get_task_info(task),
            self.execution_mode,
            self.get_result_info(result),
            time.time() - start_time,
        )

    def handle_task_error(self, task, exception: Exception):
        """
        统一处理异常任务

        :param task: 发生异常的任务
        :param exception: 捕获的异常
        :return 是否需要重试
        """
        task_id = self.get_task_id(task)
        retry_time = self.retry_time_dict.setdefault(task_id, 0)

        # 基于异常类型决定重试策略
        if (
            isinstance(exception, self.retry_exceptions)
            and retry_time < self.max_retries
        ):
            self.processed_set.remove(task_id)
            self.task_queues[0].put(task) # 只在第一个队列存放retry task
            
            self.progress_manager.add_total(1)
            self.retry_time_dict[task_id] += 1
            self.task_logger.task_retry(
                self.func.__name__, self.get_task_info(task), self.retry_time_dict[task_id], exception
            )
        else:
            # 如果不是可重试的异常，直接将任务标记为失败
            if self.enable_result_cache:
                self.error_dict[task] = exception

            # ✅ 清理 retry_time_dict
            self.retry_time_dict.pop(task_id, None)

            self.update_error_counter()
            self.put_fail_queue(task, exception)
            self.task_logger.task_error(
                self.func.__name__, self.get_task_info(task), exception
            )

    async def handle_task_error_async(self, task, exception: Exception):
        """
        统一处理任务异常, 异步版本

        :param task: 发生异常的任务
        :param exception: 捕获的异常
        :return 是否需要重试
        """
        task_id = self.get_task_id(task)
        retry_time = self.retry_time_dict.setdefault(task_id, 0)

        # 基于异常类型决定重试策略
        if (
            isinstance(exception, self.retry_exceptions)
            and retry_time < self.max_retries
        ):
            self.processed_set.remove(task_id)
            await self.task_queues[0].put(task) # 只在第一个队列存放retry task
            
            self.progress_manager.add_total(1)
            self.retry_time_dict[task_id] += 1
            self.task_logger.task_retry(
                self.func.__name__, self.get_task_info(task), self.retry_time_dict[task_id], exception
            )
        else:
            # 如果不是可重试的异常，直接将任务标记为失败
            if self.enable_result_cache:
                self.error_dict[task] = exception

            # ✅ 清理 retry_time_dict
            self.retry_time_dict.pop(task_id, None)

            self.update_error_counter()
            await self.put_fail_queue_async(task, exception)
            self.task_logger.task_error(
                self.func.__name__, self.get_task_info(task), exception
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

        total_tasks = self.put_task_queues(task_source)
        self.terminate_task_queues()
        self.task_logger.start_manager(
            self.func.__name__, total_tasks, self.execution_mode, self.worker_limit
        )

        # 根据模式运行对应的任务处理函数
        if self.execution_mode == "thread":
            self.run_with_executor(self.thread_pool)
        elif self.execution_mode == "process":
            self.run_with_executor(self.process_pool)
            # cleanup_mpqueue(self.task_queues)
        elif self.execution_mode == "async":
            asyncio.run(self.run_in_async())
        else:
            self.set_execution_mode("serial")
            self.run_in_serial()

        self.progress_manager.close()
        self.task_logger.end_manager(
            self.func.__name__,
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

        total_tasks = await self.put_task_queues_async(task_source)
        await self.terminate_task_queues_async()
        self.task_logger.start_manager(
            self.func.__name__, total_tasks, "async(await)", self.worker_limit
        )

        await self.run_in_async()

        self.progress_manager.close()
        self.task_logger.end_manager(
            self.func.__name__,
            self.execution_mode,
            time.time() - start_time,
            self.success_counter.value,
            self.error_counter.value,
            self.duplicate_counter.value,
        )
        self.log_listener.stop()

    def start_stage(self, input_queues: List[MPQueue], output_queues: List[MPQueue], fail_queue: MPQueue, logger_queue: MPQueue):
        """
        根据 start_type 的值，选择串行、并行执行任务

        :param input_queues: 输入队列
        :param output_queue: 输出队列
        :param fail_queue: 失败队列
        """
        start_time = time.time()
        self.active = True
        self.init_progress()
        self.init_env(input_queues, output_queues, fail_queue, logger_queue)
        self.task_logger.start_stage(
            self.stage_name, self.func.__name__, self.execution_mode, self.worker_limit
        )

        # 根据模式运行对应的任务处理函数
        if self.execution_mode == "thread":
            self.run_with_executor(self.thread_pool)
        else:
            self.run_in_serial()

        # cleanup_mpqueue(input_queues) # 会影响之后finalize_nodes
        self.release_pool()
        self.put_result_queues(TERMINATION_SIGNAL)
        
        self.progress_manager.close()
        self.task_logger.end_stage(
            self.stage_name,
            self.func.__name__,
            self.execution_mode,
            time.time() - start_time,
            self.success_counter.value,
            self.error_counter.value,
            self.duplicate_counter.value,
        )

    def run_in_serial(self):
        """
        串行地执行任务
        """

        # 从队列中依次获取任务并执行
        while True:
            task = self.get_task_queues()
            task_id = self.get_task_id(task)
            self.task_logger._log("TRACE",
                f"Task {task} is submitted to {self.func.__name__}"
            )
            if isinstance(task, TerminationSignal):
                # progress_manager.update(1)
                break
            elif self.is_duplicate(task_id):
                self.deal_dupliacte(task)
                self.progress_manager.update(1)
                continue
            self.processed_set.add(task_id)
            try:
                start_time = time.time()
                result = self.func(*self.get_args(task))
                self.process_task_success(task, result, start_time)
            except Exception as error:
                self.handle_task_error(task, error)
            self.progress_manager.update(1)

        self.terminated_queue_set = set()

        if not are_queues_empty(self.task_queues):
            self.task_logger._log("DEBUG", f"Retrying tasks for '{self.func.__name__}'")
            self.terminate_task_queues()
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

        def on_task_done(future, task, progress_manager: ProgressManager):
            # 回调函数中处理任务结果
            progress_manager.update(1)
            try:
                result = future.result()
                start_time = task_start_dict[task]
                self.process_task_success(task, result, start_time)
            except Exception as error:
                self.handle_task_error(task, error)
            # 任务完成后减少in_flight计数
            with in_flight_lock:
                nonlocal in_flight
                in_flight -= 1
                if in_flight == 0:
                    all_done_event.set()

        # 从任务队列中提交任务到执行池
        while True:
            task = self.get_task_queues()
            task_id = self.get_task_id(task)
            self.task_logger._log("TRACE",
                f"Task {task} is submitted to {self.func.__name__}"
            )

            if isinstance(task, TerminationSignal):
                # 收到终止信号后不再提交新任务
                # progress_manager.update(1)
                break
            elif self.is_duplicate(task_id):
                self.deal_dupliacte(task)
                self.progress_manager.update(1)
                continue
            self.processed_set.add(task_id)

            # 提交新任务时增加in_flight计数，并清除完成事件
            with in_flight_lock:
                in_flight += 1
                all_done_event.clear()

            task_start_dict[task] = time.time()
            future = executor.submit(self.func, *self.get_args(task))
            future.add_done_callback(
                lambda f, t=task: on_task_done(f, t, self.progress_manager)
            )

        # 等待所有已提交任务完成（包括回调）
        all_done_event.wait()

        # 所有任务和回调都完成了，现在可以安全关闭进度条
        self.terminated_queue_set = set()

        if not are_queues_empty(self.task_queues):
            self.task_logger._log("DEBUG", f"Retrying tasks for '{self.func.__name__}'")
            self.terminate_task_queues()
            self.run_with_executor(executor)

    async def run_in_async(self):
        """
        异步地执行任务，限制并发数量
        """
        semaphore = asyncio.Semaphore(self.worker_limit)  # 限制并发数量

        async def sem_task(task):
            start_time = time.time()  # 记录任务开始时间
            async with semaphore:  # 使用信号量限制并发
                result = await self._run_single_task(task)
                return task, result, start_time  # 返回 task, result 和 start_time

        # 创建异步任务列表
        async_tasks = []

        while True:
            task = await self.get_task_queues_async()
            task_id = self.get_task_id(task)
            self.task_logger._log("TRACE",
                f"Task {task} is submitted to {self.func.__name__}"
            )
            if isinstance(task, TerminationSignal):
                break
            elif self.is_duplicate(task_id):
                self.deal_dupliacte(task)
                self.progress_manager.update(1)
                continue
            self.processed_set.add(task_id)
            async_tasks.append(sem_task(task))  # 使用信号量包裹的任务

        # 并发运行所有任务
        for task, result, start_time in await asyncio.gather(
            *async_tasks, return_exceptions=True
        ):
            if not isinstance(result, Exception):
                await self.process_task_success_async(task, result, start_time)
            else:
                await self.handle_task_error_async(task, result)
            self.progress_manager.update(1)

        self.terminated_queue_set = set()

        if not await are_queues_empty_async(self.task_queues):
            self.task_logger._log("DEBUG", f"Retrying tasks for '{self.func.__name__}'")
            await self.terminate_task_queues_async()
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
        self.init_state()
        self.start(task_list)
        return time.time() - start

    def test_methods(self, task_source: list | tuple | set) -> dict:
        """
        测试多种方法
        """
        # 如果 task_source 是生成器或一次性可迭代对象，需要提前转化成列表
        # 确保对不同模式的测试使用同一批任务数据
        task_list = list(task_source)

        results = {}
        for mode in ["serial", "thread", "process"]:
            results[f"run_in_{mode}"] = self.test_method(mode, task_list)
        return results

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release_queue()
