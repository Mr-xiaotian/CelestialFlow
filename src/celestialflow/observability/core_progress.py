# observability/core_progress.py
from __future__ import annotations

from tqdm import tqdm

from .core_observer import TaskObserver


class TaskProgress(TaskObserver):
    """基于 tqdm 的进度条观察者"""

    def on_start(self, name: str, total: int) -> None:
        self._bar = tqdm(total=total, desc=name)

    def on_task_success(self, count: int = 1) -> None:
        self._bar.update(count)

    def on_task_fail(self, count: int = 1) -> None:
        self._bar.update(count)

    def on_task_duplicate(self, count: int = 1) -> None:
        self._bar.update(count)

    def on_tasks_added(self, count: int) -> None:
        if count:
            self._bar.total += count
            self._bar.refresh()

    def on_finish(self) -> None:
        self._bar.close()
