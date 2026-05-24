# observability/core_progress.py
from __future__ import annotations

from typing import Any

from tqdm import tqdm

from .core_observer import BaseObserver


class TaskProgress(BaseObserver):
    """基于 tqdm 的进度条观察者"""

    _bar: Any  # pyright: ignore[reportUninitializedInstanceVariable]

    def on_start(self, name: str, total: int) -> None:  # pyright: ignore[reportImplicitOverride]
        """
        初始化进度条

        :param name: 进度条标题
        :param total: 任务总数
        """
        self._bar = tqdm(total=total, desc=name)

    def on_task_success(self, count: int = 1) -> None:  # pyright: ignore[reportImplicitOverride]
        """
        更新成功进度

        :param count: 成功任务数量，默认 1
        """
        _ = self._bar.update(count)

    def on_task_fail(self, count: int = 1) -> None:  # pyright: ignore[reportImplicitOverride]
        """
        更新失败进度

        :param count: 失败任务数量，默认 1
        """
        _ = self._bar.update(count)

    def on_task_duplicate(self, count: int = 1) -> None:  # pyright: ignore[reportImplicitOverride]
        """
        更新重复进度

        :param count: 重复任务数量，默认 1
        """
        _ = self._bar.update(count)

    def on_tasks_added(self, count: int) -> None:  # pyright: ignore[reportImplicitOverride]
        """
        扩增进度条总量

        :param count: 新增任务数量
        """
        if count:
            self._bar.total += count
            self._bar.refresh()

    def on_finish(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """关闭进度条"""
        self._bar.close()
