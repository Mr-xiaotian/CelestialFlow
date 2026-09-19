# runtime/core_metrics.py
from __future__ import annotations

import time
from threading import Lock
from typing import TYPE_CHECKING

from ..runtime.util_types import StageStatus
from .util_types import ValueWrapper

if TYPE_CHECKING:
    from ..observability import BaseObserver


class TaskMetrics:
    """
    任务指标统计类

    负责管理任务执行过程中的各项指标统计，包括成功、失败、重复任务的计数，
    以及可重试异常类型和去重逻辑。
    """

    lock: Lock
    enable_duplicate_check: bool
    retry_exceptions: tuple[type[Exception], ...]
    external_input_counter: ValueWrapper
    success_counter: ValueWrapper
    fail_counter: ValueWrapper
    duplicate_counter: ValueWrapper
    upstream_counter: dict[str, ValueWrapper]
    downstream_counter: dict[str, ValueWrapper]
    processed_set: set[bytes]
    busy_seconds: float        # 已闭合的忙碌时间片之和
    _in_flight: int            # 正在执行的任务数
    _busy_since: float | None  # 当前时间片起点

    # ==== 初始化 ====

    def __init__(
        self,
        enable_duplicate_check: bool = False,
    ):
        """
        初始化 TaskMetrics

        :param enable_duplicate_check: 是否启用重复任务检查，默认值为 False
        """
        self.enable_duplicate_check = enable_duplicate_check
        self.retry_exceptions = ()
        self._observers: list[BaseObserver] = []
        self._status = int(StageStatus.NOT_STARTED)
        self.busy_seconds = 0.0
        self._in_flight = 0
        self._busy_since = None

        self.lock = Lock()
        self._init_counter()
        self.reset_state()

    def _init_counter(self) -> None:
        """
        初始化计数器
        """

        # 统一使用同一把线程锁，保证 execution_mode 切换时 counter 对象保持稳定。
        self.external_input_counter = ValueWrapper(value=0, lock=self.lock)
        self.success_counter = ValueWrapper(value=0, lock=self.lock)
        self.fail_counter = ValueWrapper(value=0, lock=self.lock)
        self.duplicate_counter = ValueWrapper(value=0, lock=self.lock)

        self.upstream_counter = {}
        self.downstream_counter = {}

    # ==== 重置 ====

    def reset_state(self) -> None:
        """
        重置统计状态
        清空已处理任务集合。

        - processed_set：用于重复检测
        """
        self.processed_set = set()  # 已处理任务哈希集合

    # ==== 观察者 ====

    def add_observer(self, observer: BaseObserver) -> None:
        """
        注册观察者。

        :param observer: 要注册的观察者实例
        """
        self._observers.append(observer)

    def remove_observer(self, observer: BaseObserver) -> None:
        """
        移除观察者。

        :param observer: 要移除的观察者实例
        """
        self._observers.remove(observer)

    # ==== 去重 ====

    def is_duplicate(self, task_hash: bytes) -> bool:
        """
        检查任务是否重复。

        该方法仅在节点工作线程中被串行调用，因此检查与记录之间无需额外加锁。

        :param task_hash: 任务的哈希值
        :return: 如果启用了去重检查且任务哈希存在于已处理集合中，返回 True；否则返回 False。
        """
        if not self.enable_duplicate_check:
            return False
        if task_hash not in self.processed_set:
            self.add_processed_set(task_hash)
            return False

        return True

    def add_processed_set(self, task_hash: bytes) -> None:
        """
        将任务添加到已处理集合
        用于后续的去重检查。

        :param task_hash: 任务的哈希值
        """
        if not self.enable_duplicate_check:
            return
        with self.lock:
            self.processed_set.add(task_hash)

    # ==== 重试 ====

    def set_retry_exceptions(self, *exceptions: type[Exception]) -> None:
        """
        添加需要重试的异常类型

        :param *exceptions: 异常类列表
        """
        self.retry_exceptions = self.retry_exceptions + tuple(exceptions)

    # ==== 设定 ====

    def set_upstream_counter(self, name: str, counter: ValueWrapper) -> None:
        """
        添加上游任务计数器
        用于统计从上游节点接收的任务数量。

        :param name: 上游节点的唯一名称
        :param counter: 上游传输任务计数器实例
        """
        self.upstream_counter[name] = counter

    def set_downstream_counter(self, name: str, counter: ValueWrapper) -> None:
        """
        添加下游任务计数器
        用于统计向下游节点发送的任务数量。

        :param name: 下游节点的唯一名称
        :param counter: 任务总数计数器实例
        """
        self.downstream_counter[name] = counter

    # ==== 任务计数器 ====

    def add_external_input_count(self, add_count: int = 1) -> None:
        """
        更新外部注入任务计数器

        增加由外部直接注入的任务数量（经由 ``put_task`` 进入节点的任务）。

        :param add_count: 增加的外部注入任务数
        """
        self.external_input_counter.add(add_count)
        for observer in self._observers:
            observer.on_tasks_added(add_count)

    def add_success_count(self, count: int = 1) -> None:
        """
        更新成功任务计数器

        线程安全地增加成功任务的数量。

        :param count: 增加的成功任务数量，默认值为 1。
        """
        self.success_counter.add(count)
        for observer in self._observers:
            observer.on_task_success(count)

    def add_fail_count(self, count: int = 1) -> None:
        """
        更新失败任务计数器

        线程安全地增加失败任务的数量。

        :param count: 增加的失败任务数量，默认值为 1。
        """
        self.fail_counter.add(count)
        for observer in self._observers:
            observer.on_task_fail(count)

    def add_duplicate_count(self, count: int = 1) -> None:
        """
        更新重复任务计数器

        线程安全地增加重复任务的数量。

        :param count: 增加的重复任务数量，默认值为 1。
        """
        self.duplicate_counter.add(count)
        for observer in self._observers:
            observer.on_task_duplicate(count)

    def add_downstream_count(self, name: str, count: int = 1) -> None:
        """
        更新下游任务计数器

        线程安全地增加下游任务的数量。

        :param name: 下游节点的唯一名称
        :param count: 增加的下游任务数量，默认值为 1。
        """
        self.downstream_counter[name].add(count)

    # ==== 启动与结束 ====

    def on_start(self, _name: str, _total: int) -> None:
        """
        广播执行器启动事件。

        :param _name: 执行器全名
        :param _total: 任务总数
        :return: ``None``
        """
        self._status = int(StageStatus.RUNNING)
        for observer in self._observers:
            observer.on_start(_name, _total)

    def on_finish(self) -> None:
        """
        广播执行器结束事件。

        :return: ``None``
        """
        self._status = int(StageStatus.STOPPED)
        for observer in self._observers:
            observer.on_finish()

    # ==== 查询 ====

    def get_external_input_count(self) -> int:
        """
        获取外部注入的任务数量

        :return: 当前由外部直接注入的任务总数
        """
        return self.external_input_counter.get()

    def get_upstream_input_count(self) -> int:
        """
        获取上游提供的任务数量

        :return: 当前从各上游节点接收的任务总数
        """
        input_count = 0
        for counter in self.upstream_counter.values():
            input_count += counter.get()
        return input_count

    def get_input_count(self) -> int:
        """
        获取当前的任务总数

        外部注入任务数与上游提供任务数之和。

        :return: 当前的任务总数
        """
        return self.get_external_input_count() + self.get_upstream_input_count()

    def get_success_count(self) -> int:
        """
        获取当前的成功任务数

        :return: 当前的成功任务数
        """
        return self.success_counter.get()

    def get_fail_count(self) -> int:
        """
        获取当前的失败任务数

        :return: 当前的失败任务数
        """
        return self.fail_counter.get()

    def get_duplicate_count(self) -> int:
        """
        获取当前的重复任务数

        :return: 当前的重复任务数
        """
        return self.duplicate_counter.get()

    def is_tasks_finished(self) -> bool:
        """
        检查所有任务是否已完成

        通过比较总输入任务数与已处理（成功+失败+重复）的任务数来判断。

        :return: 如果所有任务都已处理完毕，返回 True；否则返回 False。
        """
        total = self.get_input_count()

        with self.lock:
            processed = (
                self.success_counter.value
                + self.fail_counter.value
                + self.duplicate_counter.value
            )
        return total == processed

    def get_counts(self) -> dict[str, int]:
        """
        获取当前的统计数据字典

        :return: 包含以下字段的字典：
                - tasks_input: 输入任务总数（外部注入与上游提供之和）
                - tasks_succeeded: 成功任务数
                - tasks_failed: 失败任务数
                - tasks_duplicated: 重复任务数
                - tasks_processed: 已处理任务总数
                - tasks_pending: 等待处理任务数
        """
        input_count = self.get_input_count()

        with self.lock:
            succeeded = self.success_counter.value
            failed = self.fail_counter.value
            duplicated = self.duplicate_counter.value

        processed = succeeded + failed + duplicated
        pending = max(0, input_count - processed)

        return {
            "tasks_input": input_count,
            "tasks_succeeded": succeeded,
            "tasks_failed": failed,
            "tasks_duplicated": duplicated,
            "tasks_processed": processed,
            "tasks_pending": pending,
        }

    def get_upstream_counts(self) -> dict[str, int]:
        """
        获取各上游节点传输给当前节点的任务数量。

        :return: 上游名称到任务数量的映射；无上游时返回空字典
        """
        upstream_counts: dict[str, int] = {}
        for name, count in self.upstream_counter.items():
            upstream_counts[name] = count.get()
        return upstream_counts

    def get_downstream_counts(self) -> dict[str, int]:
        """
        获取当前节点传输给各下游节点的任务数量。

        :return: 下游名称到任务数量的映射；无下游时返回空字典
        """
        downstream_counts: dict[str, int] = {}
        for name, count in self.downstream_counter.items():
            downstream_counts[name] = count.get()
        return downstream_counts

    def get_retry_error_type_names(self) -> set[str]:
        """
        获取当前执行器允许从持久化失败记录中恢复的错误类型名称集合。

        :return: 可重试错误类型名称集合
        :rtype: set[str]
        """
        return {exception_type.__name__ for exception_type in self.retry_exceptions}

    def get_status(self) -> StageStatus:
        """读取当前状态（返回 StageStatus 枚举）。"""
        return StageStatus(self._status)

    # ==== 消耗时间 ====

    def begin_task(self) -> None:
        """一个任务开始实际执行。"""
        with self.lock:
            self._in_flight += 1
            if self._in_flight == 1:  # 0 → 1：节点从闲变忙
                self._busy_since = time.perf_counter()

    def end_task(self) -> None:
        """一个任务执行结束（含重试全部结束）。"""
        with self.lock:
            self._in_flight -= 1
            if self._in_flight == 0 and self._busy_since is not None:  # 1 → 0：节点从忙变闲
                self.busy_seconds += time.perf_counter() - self._busy_since
                self._busy_since = None

    def get_elapsed(self) -> float:
        """累计忙碌墙钟时间（秒），含当前尚未闭合的时间片。"""
        with self.lock:
            if self._busy_since is None:
                return self.busy_seconds
            return self.busy_seconds + time.perf_counter() - self._busy_since
