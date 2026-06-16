from typing import Any

from demo_utils import fibonacci, fibonacci_async

from celestialflow import BaseObserver, TaskExecutor, TaskProgress


class LoggingObserver(BaseObserver):
    def __init__(self) -> None:
        self.name = ""
        self.total = 0
        self.succeeded = 0
        self.failed = 0
        self.duplicated = 0

    def on_start(self, name: str, total: int) -> None:
        self.name = name
        self.total = total
        print(f"[observer] start executor={name}, total={total}")

    def on_task_success(self, count: int = 1) -> None:
        self.succeeded += count
        print(f"[observer] success +{count}, succeeded={self.succeeded}")

    def on_task_fail(self, count: int = 1) -> None:
        self.failed += count
        print(f"[observer] fail +{count}, failed={self.failed}")

    def on_task_duplicate(self, count: int = 1) -> None:
        self.duplicated += count
        print(f"[observer] duplicate +{count}, duplicated={self.duplicated}")

    def on_tasks_added(self, count: int) -> None:
        self.total += count
        print(f"[observer] tasks added +{count}, total={self.total}")

    def on_finish(self) -> None:
        print(
            "[observer] finish "
            f"executor={self.name}, total={self.total}, "
            f"succeeded={self.succeeded}, failed={self.failed}, duplicated={self.duplicated}"
        )


def demo_progress_observer() -> None:
    test_task: list[Any] = list(range(25, 32))

    executor = TaskExecutor(
        "FibonacciSerial2",
        fibonacci,
        execution_mode="serial",
        max_workers=6,
        max_retries=1,
    )
    executor.add_observer(TaskProgress())

    executor.start(test_task)


def demo_custom_observer() -> None:
    test_task: list[Any] = list(range(25, 32))

    executor = TaskExecutor(
        "FibonacciSerial2",
        fibonacci,
        execution_mode="serial",
        max_workers=6,
        max_retries=1,
    )
    executor.add_observer(LoggingObserver())

    executor.start(test_task)


if __name__ == "__main__":
    demo_custom_observer()
