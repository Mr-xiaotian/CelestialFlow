from typing import Any

from demo_utils import fibonacci
from tqdm import tqdm

from celestialflow import Observer, PrintObserver, TaskExecutor
from celestialflow.observability import (
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
        """初始化进度条观察者，进度条延迟到 on_node_start 时创建"""
        self._bar = None
        self._total = 0

    def on_node_start(self, event: NodeStartEvent) -> None:
        """
        创建进度条，总量取启动前已注入的任务数

        :param event: 节点启动事件
        """
        self._bar = tqdm(total=self._total)

    def on_task_input(self, event: TaskInputEvent) -> None:
        """
        扩增进度条总量

        该回调可能先于 ``on_node_start`` 到达，此时仅累加总量，待进度条创建后一并应用。

        :param event: 任务输入事件
        """
        self._total += 1
        if self._bar is not None:
            self._bar.total += 1
            self._bar.refresh()

    def on_task_success(self, event: TaskSuccessEvent) -> None:
        """
        更新成功进度

        :param event: 任务成功事件
        """
        self._advance(1)

    def on_task_fail(self, event: TaskFailEvent) -> None:
        """
        更新失败进度

        :param event: 任务失败事件
        """
        self._advance(1)

    def on_task_skip(self, event: TaskSkipEvent) -> None:
        """
        更新跳过进度

        :param event: 任务跳过事件
        """
        self._advance(1)

    def on_node_end(self, event: NodeEndEvent) -> None:
        """
        关闭进度条

        :param event: 节点结束事件
        """
        if self._bar is not None:
            self._bar.close()

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
