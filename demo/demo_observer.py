from typing import Any

from demo_utils import fibonacci
from tqdm import tqdm

from celestialflow import Observer, PrintObserver, TaskExecutor
from celestialflow.observer import (
    Event,
    NodeEndEvent,
    NodeStartEvent,
    TaskFailEvent,
    TaskInputEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
)


class TaskProgress(Observer):
    """基于 tqdm 的进度条观察者"""

    _bar: tqdm[Any] | None
    _total: int

    def __init__(self) -> None:
        """初始化进度条观察者，进度条延迟到节点启动事件时创建"""
        self._bar = None
        self._total = 0

    def on_event(self, event: Event) -> None:
        """
        接收并处理观测事件，按事件类型推进进度条。

        ``TaskInputEvent`` 可能先于 ``NodeStartEvent`` 到达，此时仅累加总量，
        待进度条创建后一并应用。

        :param event: 任意观测事件
        """
        match event:
            case NodeStartEvent():
                self._bar = tqdm(total=self._total)
            case NodeEndEvent():
                if self._bar is not None:
                    self._bar.close()
            case TaskInputEvent():
                self._total += 1
                if self._bar is not None:
                    self._bar.total += 1
                    self._bar.refresh()
            case TaskSuccessEvent() | TaskFailEvent() | TaskSkipEvent():
                self._advance(1)

    def _advance(self, count: int) -> None:
        """
        推进进度条

        :param count: 本次推进的数量
        """
        if self._bar is not None:
            _ = self._bar.update(count)


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

    executor.run(test_task)


def demo_print_observer() -> None:
    test_task: list[Any] = list(range(25, 32))

    executor = TaskExecutor(
        "FibonacciSerial2",
        fibonacci,
        execution_mode="serial",
        max_workers=6,
        max_retries=1,
    )
    executor.add_observer(PrintObserver(executor.get_name()))

    executor.run(test_task)


if __name__ == "__main__":
    demo_progress_observer()
    demo_print_observer()
