# runtime/core_metrics.py
import asyncio
from threading import Lock

from .util_factories import (
    make_counter,
)
from .util_types import SumCounter


class TaskMetrics:
    """
    任务指标统计类

    负责管理任务执行过程中的各项指标统计，包括成功、失败、重复任务的计数，
    以及可重试异常类型和去重逻辑。
    """

    def __init__(
        self,
        execution_mode: str,
        max_retries: int = 1,
        enable_duplicate_check: bool = False,
    ):
        """
        初始化 TaskMetrics

        :param execution_mode: 任务执行模式，可选值为 "thread" 或 "async"
        :param max_retries: 最大重试次数，默认值为 1
        :param enable_duplicate_check: 是否启用重复任务检查，默认值为 False
        """
        self.execution_mode = execution_mode
        self.max_retries = max_retries
        self.enable_duplicate_check = enable_duplicate_check

        self.retry_exceptions: tuple[type[Exception], ...] = ()
        self._init_counter()
        self.reset_state()

    def _init_counter(self) -> None:
        """
        初始化计数器（按 execution_mode 选择实现）
        """
        mode = self.execution_mode

        # thread 模式下，让三个 counter 共用同一把锁（减少开销，也更一致）
        lock = Lock() if mode == "thread" else None

        self.task_counter = SumCounter(mode=mode)
        self.success_counter = make_counter(mode, lock=lock)
        self.error_counter = make_counter(mode, lock=lock)
        self.duplicate_counter = make_counter(mode, lock=lock)

    def reset_counter(self) -> None:
        """
        重置计数器
        """
        self.task_counter.reset()
        self.success_counter.value = 0
        self.error_counter.value = 0
        self.duplicate_counter.value = 0

    def reset_state(self) -> None:
        """
        重置统计状态
        清空已处理任务集合。

        - processed_set：用于重复检测
        """
        self.processed_set: set[str] = set()  # task_hash

    def set_execution_mode(self, execution_mode: str) -> None:
        """
        设置任务执行模式

        :param execution_mode: 任务执行模式，可选值为 "thread" 或 "async"
        """
        self.execution_mode = execution_mode
        self._init_counter()

    def is_duplicate(self, task_hash: str) -> bool:
        """
        检查任务是否重复

        :param task_hash: 任务的哈希值
        :return: 如果启用了去重检查且任务哈希存在于已处理集合中，返回 True；否则返回 False。
        """
        if not self.enable_duplicate_check:
            return False
        if task_hash not in self.processed_set:
            self.add_processed_set(task_hash)
            return False

        return True

    def add_processed_set(self, task_hash: str) -> None:
        """
        将任务添加到已处理集合
        用于后续的去重检查。

        :param task_hash: 任务的哈希值
        """
        if self.enable_duplicate_check:
            self.processed_set.add(task_hash)

    def discard_processed_set(self, task_hash: str) -> None:
        """
        从已处理集合中移除任务
        用于在任务处理完成后，从去重集合中移除已处理任务。

        :param task_hash: 任务的哈希值
        """
        if self.enable_duplicate_check:
            self.processed_set.discard(task_hash)

    # retry
    def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
        """
        添加需要重试的异常类型

        :param *exceptions: 异常类列表
        """
        self.retry_exceptions = self.retry_exceptions + tuple(exceptions)

    # counter
    def append_task_counter(self, counter) -> None:
        """
        添加任务总数计数器

        :param counter: 任务总数计数器实例
        """
        self.task_counter.append_counter(counter)

    def add_task_count(self, add_count: int = 1):
        """
        更新任务总数计数器

        增加已接收到的任务总数。
        """
        self.task_counter.add_init_value(add_count)

    def add_success_count(self, count: int = 1):
        """
        更新成功任务计数器

        线程安全地增加成功任务的数量。

        :param count: 增加的成功任务数量，默认值为 1。
        """
        with self.success_counter.get_lock():
            self.success_counter.value += count

    async def add_success_count_async(self, count: int = 1):
        """
        异步更新成功任务计数器

        在独立线程中执行 add_success_count，避免阻塞事件循环。

        :param count: 增加的成功任务数量，默认值为 1。
        """
        await asyncio.to_thread(self.add_success_count, count)

    def add_error_count(self, count: int = 1):
        """
        更新失败任务计数器

        线程安全地增加失败任务的数量。

        :param count: 增加的失败任务数量，默认值为 1。
        """
        with self.error_counter.get_lock():
            self.error_counter.value += count

    def add_duplicate_count(self, count: int = 1):
        """
        更新重复任务计数器

        线程安全地增加重复任务的数量。

        :param count: 增加的重复任务数量，默认值为 1。
        """
        with self.duplicate_counter.get_lock():
            self.duplicate_counter.value += count

    def is_tasks_finished(self) -> bool:
        """
        检查所有任务是否已完成

        通过比较总输入任务数与已处理（成功+失败+重复）的任务数来判断。

        Returns:
            bool: 如果所有任务都已处理完毕，返回 True；否则返回 False。
        """
        processed = (
            self.success_counter.value
            + self.error_counter.value
            + self.duplicate_counter.value
        )
        return self.task_counter.value == processed

    def get_task_count(self) -> int:
        """
        获取当前的任务总数

        :return: 当前的任务总数
        """
        return self.task_counter.value

    def get_success_count(self) -> int:
        """
        获取当前的成功任务数

        :return: 当前的成功任务数
        """
        return self.success_counter.value

    def get_error_count(self) -> int:
        """
        获取当前的失败任务数

        :return: 当前的失败任务数
        """
        return self.error_counter.value

    def get_duplicate_count(self) -> int:
        """
        获取当前的重复任务数

        :return: 当前的重复任务数
        """
        return self.duplicate_counter.value

    def get_counts(self) -> dict[str, int]:
        """
        获取当前的统计数据字典

        :return: 包含以下字段的字典：
                - tasks_input: 输入任务总数
                - tasks_successed: 成功任务数
                - tasks_failed: 失败任务数
                - tasks_duplicated: 重复任务数
                - tasks_processed: 已处理任务总数
                - tasks_pending: 等待处理任务数
        """
        input_count = self.task_counter.value
        successed = self.success_counter.value
        failed = self.error_counter.value
        duplicated = self.duplicate_counter.value
        processed = successed + failed + duplicated
        pending = max(0, input_count - processed)

        return {
            "tasks_input": input_count,
            "tasks_successed": successed,
            "tasks_failed": failed,
            "tasks_duplicated": duplicated,
            "tasks_processed": processed,
            "tasks_pending": pending,
        }
