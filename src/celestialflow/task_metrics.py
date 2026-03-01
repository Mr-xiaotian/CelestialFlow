import asyncio
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .task_executor import TaskExecutor

class TaskMetrics:
    """
    任务指标统计类

    负责管理任务执行过程中的各项指标统计，包括成功、失败、重复任务的计数，
    以及重试异常的管理和去重逻辑。
    """
    def __init__(self, executor: "TaskExecutor"):
        """
        初始化 TaskMetrics

        Args:
            executor (TaskExecutor): 关联的任务执行器实例
        """
        self.executor = executor
        self.retry_exceptions = tuple()
        self.reset_state()

    def reset_state(self):
        """
        重置统计状态

        清空重试时间记录和已处理任务集合。
        """
        self.retry_time_dict = {}
        self.processed_set = set()

    def add_retry_exceptions(self, *exceptions):
        """
        添加需要重试的异常类型

        Args:
            *exceptions: 异常类列表
        """
        self.retry_exceptions = self.retry_exceptions + tuple(exceptions)

    def update_task_counter(self):
        """
        更新任务总数计数器

        增加已接收到的任务总数。
        """
        self.executor.task_counter.add_init_value(1)

    def update_success_counter(self):
        """
        更新成功任务计数器

        线程安全地增加成功任务的数量。
        """
        with self.executor.success_counter.get_lock():
            self.executor.success_counter.value += 1

    async def update_success_counter_async(self):
        """
        异步更新成功任务计数器

        在独立线程中执行 update_success_counter，避免阻塞事件循环。
        """
        await asyncio.to_thread(self.update_success_counter)

    def update_error_counter(self):
        """
        更新失败任务计数器

        线程安全地增加失败任务的数量。
        """
        with self.executor.error_counter.get_lock():
            self.executor.error_counter.value += 1

    def update_duplicate_counter(self):
        """
        更新重复任务计数器

        线程安全地增加重复任务的数量。
        """
        with self.executor.duplicate_counter.get_lock():
            self.executor.duplicate_counter.value += 1

    def is_tasks_finished(self) -> bool:
        """
        检查所有任务是否已完成

        通过比较总输入任务数与已处理（成功+失败+重复）的任务数来判断。

        Returns:
            bool: 如果所有任务都已处理完毕，返回 True；否则返回 False。
        """
        processed = (
            self.executor.success_counter.value
            + self.executor.error_counter.value
            + self.executor.duplicate_counter.value
        )
        return self.executor.task_counter.value == processed

    def is_duplicate(self, task_hash):
        """
        检查任务是否重复

        Args:
            task_hash: 任务的哈希值

        Returns:
            bool: 如果启用了去重检查且任务哈希存在于已处理集合中，返回 True；否则返回 False。
        """
        if not self.executor.enable_duplicate_check:
            return False
        return task_hash in self.processed_set

    def add_processed_set(self, task_hash):
        """
        将任务添加到已处理集合

        用于后续的去重检查。

        Args:
            task_hash: 任务的哈希值
        """
        if self.executor.enable_duplicate_check:
            self.processed_set.add(task_hash)

    def get_counts(self) -> dict:
        """
        获取当前的统计数据字典

        Returns:
            dict: 包含以下字段的字典：
                - tasks_input: 输入任务总数
                - tasks_successed: 成功任务数
                - tasks_failed: 失败任务数
                - tasks_duplicated: 重复任务数
                - tasks_processed: 已处理任务总数
                - tasks_pending: 等待处理任务数
        """
        input_count = self.executor.task_counter.value
        successed = self.executor.success_counter.value
        failed = self.executor.error_counter.value
        duplicated = self.executor.duplicate_counter.value
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
