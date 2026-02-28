import asyncio
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .task_executor import TaskExecutor

class TaskMetrics:
    def __init__(self, executor: "TaskExecutor"):
        self.executor = executor
        self.retry_exceptions = tuple()
        self.reset_state()

    def reset_state(self):
        self.retry_time_dict = {}
        self.processed_set = set()

    def add_retry_exceptions(self, *exceptions):
        self.retry_exceptions = self.retry_exceptions + tuple(exceptions)

    def update_task_counter(self):
        self.executor.task_counter.add_init_value(1)

    def update_success_counter(self):
        with self.executor.success_counter.get_lock():
            self.executor.success_counter.value += 1

    async def update_success_counter_async(self):
        await asyncio.to_thread(self.update_success_counter)

    def update_error_counter(self):
        with self.executor.error_counter.get_lock():
            self.executor.error_counter.value += 1

    def update_duplicate_counter(self):
        with self.executor.duplicate_counter.get_lock():
            self.executor.duplicate_counter.value += 1

    def is_tasks_finished(self) -> bool:
        processed = (
            self.executor.success_counter.value
            + self.executor.error_counter.value
            + self.executor.duplicate_counter.value
        )
        return self.executor.task_counter.value == processed

    def is_duplicate(self, task_hash):
        if not self.executor.enable_duplicate_check:
            return False
        return task_hash in self.processed_set

    def add_processed_set(self, task_hash):
        if self.executor.enable_duplicate_check:
            self.processed_set.add(task_hash)

    def get_counts(self) -> dict:
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
