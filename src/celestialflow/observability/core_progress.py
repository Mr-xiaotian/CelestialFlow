# runtime/core_progress.py
from tqdm import tqdm
from tqdm.asyncio import tqdm as tqdm_asy


class TaskProgress:
    """
    任务进度条管理器
    """

    def __init__(
        self,
        total_tasks: int,
        desc: str,
        mode: str = "normal",
    ):
        """
        初始化进度条管理器

        :param total_tasks: 任务总数，用于设置进度条的总长度
        :param desc: 进度条的描述文字
        :param mode: 任务模式，可选 "async", other
        :param show_progress: 是否显示进度条
        """
        if mode == "async":
            self.progress_bar = tqdm_asy(total=total_tasks, desc=desc)
        else:
            self.progress_bar = tqdm(total=total_tasks, desc=desc)

    def update(self, n: int = 1) -> None:
        """更新进度条"""
        self.progress_bar.update(n)

    def close(self) -> None:
        """关闭进度条"""
        self.progress_bar.close()

    def refresh_total(self, total: int) -> None:
        """动态调整进度条的总任务数"""
        self.progress_bar.total = total
        self.progress_bar.refresh()

    def add_total(self, add_num: int) -> None:
        """动态增加进度条的总任务数"""
        if not add_num:
            return
        total = self.progress_bar.total + add_num
        self.refresh_total(total)


class NullTaskProgress:
    """
    空进度条管理器，用于在不需要进度条的场景下占位
    """

    def update(self, n: int = 1) -> None:
        pass

    def close(self) -> None:
        pass

    def refresh_total(self, total: int) -> None:
        pass

    def add_total(self, add_num: int) -> None:
        pass
