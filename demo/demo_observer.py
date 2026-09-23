from typing import Any

from demo_utils import fibonacci
from tqdm import tqdm

from celestialflow import BaseObserver, PrintObserver, TaskExecutor


class TaskProgress(BaseObserver):
    """基于 tqdm 的进度条观察者"""

    _bar: tqdm[Any] | None
    _total: int

    def __init__(self) -> None:
        """初始化进度条观察者，进度条延迟到 on_start 时创建"""
        self._bar = None
        self._total = 0

    def on_start(self) -> None:
        """创建进度条，总量取启动前已注入的任务数"""
        self._bar = tqdm(total=self._total)

    def on_task_success(self, count: int = 1) -> None:
        """
        更新成功进度

        :param count: 成功任务数量，默认 1
        """
        self._advance(count)

    def on_task_fail(self, count: int = 1) -> None:
        """
        更新失败进度

        :param count: 失败任务数量，默认 1
        """
        self._advance(count)

    def on_task_duplicate(self, count: int = 1) -> None:
        """
        更新重复进度

        :param count: 重复任务数量，默认 1
        """
        self._advance(count)

    def on_task_added(self, count: int) -> None:
        """
        扩增进度条总量

        该回调可能先于 ``on_start`` 到达，此时仅累加总量，待进度条创建后一并应用。

        :param count: 新增任务数量
        """
        self._total += count
        if self._bar is not None:
            self._bar.total += count
            self._bar.refresh()

    def on_finish(self) -> None:
        """关闭进度条"""
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
