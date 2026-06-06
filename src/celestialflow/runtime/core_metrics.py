# runtime/core_metrics.py
from __future__ import annotations
from threading import Lock

from .util_types import NoOpContext, SumCounter, ValueWrapper


class TaskMetrics:
    """
    任务指标统计类

    负责管理任务执行过程中的各项指标统计，包括成功、失败、重复任务的计数，
    以及可重试异常类型和去重逻辑。
    """

    lock: Lock | NoOpContext
    execution_mode: str
    enable_duplicate_check: bool
    retry_exceptions: tuple[type[Exception], ...]
    task_counter: SumCounter
    success_counter: ValueWrapper
    error_counter: ValueWrapper
    duplicate_counter: ValueWrapper
    processed_set: set[bytes]

    # ==== 初始化 ====
    def __init__(
        self,
        execution_mode: str,
        enable_duplicate_check: bool = False,
    ):
        """
        初始化 TaskMetrics

        :param execution_mode: 任务执行模式，可选值为 "serial", "thread" 或 "async"
        :param enable_duplicate_check: 是否启用重复任务检查，默认值为 False
        """
        self.execution_mode = execution_mode
        self.enable_duplicate_check = enable_duplicate_check
        self.retry_exceptions = ()

        self._init_lock()
        self._init_counter()
        self.reset_state()

    def _init_lock(self) -> None:
        """
        初始化锁对象（按 execution_mode 选择实现）
        :param execution_mode: 任务执行模式，可选值为 "serial", "thread" 或 "async"
        :param enable_duplicate_check: 是否启用重复任务检查，默认值为 False
        """
        self.lock = Lock() if self.execution_mode == "thread" else NoOpContext()

    def _init_counter(self) -> None:
        """
        初始化计数器
        """

        # thread 模式下，让四个 counter 共用同一把锁（减少开销，也更一致）
        self.task_counter = SumCounter(lock=self.lock)
        self.success_counter = ValueWrapper(value=0, lock=self.lock)
        self.error_counter = ValueWrapper(value=0, lock=self.lock)
        self.duplicate_counter = ValueWrapper(value=0, lock=self.lock)

    def reset_counter(self) -> None:
        """
        重置计数器
        """
        self.task_counter.reset()
        self.success_counter.reset()
        self.error_counter.reset()
        self.duplicate_counter.reset()

    def reset_state(self) -> None:
        """
        重置统计状态
        清空已处理任务集合。

        - processed_set：用于重复检测
        """
        self.processed_set = set()  # task_hash

    def set_execution_mode(self, execution_mode: str) -> None:
        """
        设置任务执行模式

        :param execution_mode: 任务执行模式，可选值为 "serial", "thread" 或 "async"
        """
        self.execution_mode = execution_mode
        self._init_lock()
        self._init_counter()

    # ==== 去重 ====
    def is_duplicate(self, task_hash: bytes) -> bool:
        """
        检查任务是否重复, 是原子操作
        不管有多少 worker thread, is_duplicate 本身只会被 executor thread 线性操作

        :param task_hash: 任务的哈希值
        :return: 如果启用了去重检查且任务哈希存在于已处理集合中，返回 True；否则返回 False。
        """
        if not self.enable_duplicate_check:
            return False
        if task_hash not in self.processed_set:
            self.add_processed_set(task_hash)
            return False

        return True

    def add_processed_set(self, task_hash: bytes) -> None:
        """
        将任务添加到已处理集合
        用于后续的去重检查。

        :param task_hash: 任务的哈希值
        """
        if not self.enable_duplicate_check:
            return
        with self.lock:
            self.processed_set.add(task_hash)

    # ==== 重试 ====
    def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
        """
        添加需要重试的异常类型

        :param *exceptions: 异常类列表
        """
        self.retry_exceptions = self.retry_exceptions + tuple(exceptions)

    # ==== 计数器 ====
    def append_task_counter(self, counter: ValueWrapper) -> None:
        """
        添加任务总数计数器

        :param counter: 任务总数计数器实例
        """
        self.task_counter.append_counter(counter)

    def add_task_count(self, add_count: int = 1) -> None:
        """
        更新任务总数计数器

        增加已接收到的任务总数。

        :param add_count: 增加的任务数
        """
        self.task_counter.add(add_count)

    def add_success_count(self, count: int = 1) -> None:
        """
        更新成功任务计数器

        线程安全地增加成功任务的数量。

        :param count: 增加的成功任务数量，默认值为 1。
        """
        self.success_counter.add(count)

    def add_error_count(self, count: int = 1) -> None:
        """
        更新失败任务计数器

        线程安全地增加失败任务的数量。

        :param count: 增加的失败任务数量，默认值为 1。
        """
        self.error_counter.add(count)

    def add_duplicate_count(self, count: int = 1) -> None:
        """
        更新重复任务计数器

        线程安全地增加重复任务的数量。

        :param count: 增加的重复任务数量，默认值为 1。
        """
        self.duplicate_counter.add(count)

    # ==== 查询 ====
    def is_tasks_finished(self) -> bool:
        """
        检查所有任务是否已完成

        通过比较总输入任务数与已处理（成功+失败+重复）的任务数来判断。

        :return: 如果所有任务都已处理完毕，返回 True；否则返回 False。
        """
        with self.lock:
            processed = (
                self.success_counter.value
                + self.error_counter.value
                + self.duplicate_counter.value
            )
            total = self.task_counter.value
        return total == processed

    def get_task_count(self) -> int:
        """
        获取当前的任务总数

        :return: 当前的任务总数
        """
        return self.task_counter.get()

    def get_success_count(self) -> int:
        """
        获取当前的成功任务数

        :return: 当前的成功任务数
        """
        return self.success_counter.get()

    def get_error_count(self) -> int:
        """
        获取当前的失败任务数

        :return: 当前的失败任务数
        """
        return self.error_counter.get()

    def get_duplicate_count(self) -> int:
        """
        获取当前的重复任务数

        :return: 当前的重复任务数
        """
        return self.duplicate_counter.get()

    def get_counts(self) -> dict[str, int]:
        """
        获取当前的统计数据字典

        :return: 包含以下字段的字典：
                - tasks_input: 输入任务总数
                - tasks_succeeded: 成功任务数
                - tasks_failed: 失败任务数
                - tasks_duplicated: 重复任务数
                - tasks_processed: 已处理任务总数
                - tasks_pending: 等待处理任务数
        """
        with self.lock:
            input_count = self.task_counter.value
            succeeded = self.success_counter.value
            failed = self.error_counter.value
            duplicated = self.duplicate_counter.value

        processed = succeeded + failed + duplicated
        pending = max(0, input_count - processed)

        return {
            "tasks_input": input_count,
            "tasks_succeeded": succeeded,
            "tasks_failed": failed,
            "tasks_duplicated": duplicated,
            "tasks_processed": processed,
            "tasks_pending": pending,
        }
