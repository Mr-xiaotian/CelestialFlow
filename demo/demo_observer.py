from typing import Any

from demo_utils import fibonacci
from tqdm import tqdm

from celestialflow import BaseObserver, TaskExecutor


class TaskProgress(BaseObserver):
    """基于 tqdm 的进度条观察者"""

    _bar: tqdm[Any]

    def on_start(self, name: str, total: int) -> None:
        """
        初始化进度条

        :param name: 进度条标题
        :param total: 任务总数
        """
        self._bar = tqdm(total=total, desc=name)

    def on_task_success(self, count: int = 1) -> None:
        """
        更新成功进度

        :param count: 成功任务数量，默认 1
        """
        _ = self._bar.update(count)

    def on_task_fail(self, count: int = 1) -> None:
        """
        更新失败进度

        :param count: 失败任务数量，默认 1
        """
        _ = self._bar.update(count)

    def on_task_duplicate(self, count: int = 1) -> None:
        """
        更新重复进度

        :param count: 重复任务数量，默认 1
        """
        _ = self._bar.update(count)

    def on_tasks_added(self, count: int) -> None:
        """
        扩增进度条总量

        :param count: 新增任务数量
        """
        if count:
            self._bar.total += count
            self._bar.refresh()

    def on_finish(self) -> None:
        """关闭进度条"""
        self._bar.close()


class PrintObserver(BaseObserver):
    """基于日志输出的观察者，将任务执行进度通过 print 输出到控制台"""

    def __init__(self) -> None:
        """初始化日志观察者，将所有计数器置零"""
        self.name = ""
        self.total = 0
        self.succeeded = 0
        self.failed = 0
        self.duplicated = 0

    def on_start(self, name: str, total: int) -> None:
        """
        任务执行器启动时的回调

        :param name: 执行器名称
        :param total: 任务总数
        """
        self.name = name
        self.total = total
        print(f"[observer] start executor={name}, total={total}")

    def on_task_success(self, count: int = 1) -> None:
        """
        任务成功执行时的回调

        :param count: 本次成功执行的任务数量，默认 1
        """
        self.succeeded += count
        print(f"[observer] success +{count}, succeeded={self.succeeded}")

    def on_task_fail(self, count: int = 1) -> None:
        """
        任务执行失败时的回调

        :param count: 本次失败的任务数量，默认 1
        """
        self.failed += count
        print(f"[observer] fail +{count}, failed={self.failed}")

    def on_task_duplicate(self, count: int = 1) -> None:
        """
        检测到重复任务时的回调

        :param count: 本次去重的任务数量，默认 1
        """
        self.duplicated += count
        print(f"[observer] duplicate +{count}, duplicated={self.duplicated}")

    def on_tasks_added(self, count: int) -> None:
        """
        动态添加新任务时的回调

        :param count: 新增的任务数量
        """
        self.total += count
        print(f"[observer] tasks added +{count}, total={self.total}")

    def on_finish(self) -> None:
        """任务执行器完成后的回调，打印最终统计结果"""
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
    executor.add_observer(PrintObserver())

    executor.run(test_task)


if __name__ == "__main__":
    demo_progress_observer()
    demo_print_observer()
