# stage/core_stages.py
import time
from collections.abc import Callable, Iterable
from typing import Any, cast

from ..runtime import TaskEnvelope, TaskOutQueue
from ..runtime.util_errors import InvalidOptionError
from ..runtime.util_types import ValueWrapper
from ..utils.util_format import format_repr
from .core_stage import TaskStage


# ==== TaskSplitter ====
class TaskSplitter[TItem, RItem](TaskStage[Iterable[TItem], Iterable[RItem]]):
    """TaskSplitter: 将单个任务拆分为多个子任务，注入下游队列。

    可通过 `split_item` 参数自定义对子任务的处理逻辑。
    """

    split_counter: ValueWrapper
    execution_mode: str
    split_item: Callable[[TItem], RItem]

    def __init__(
        self,
        name: str,
        split_item: Callable[[TItem], RItem] | None = None,
        *,
        stage_mode: str = "serial",
    ):
        """
        初始化 TaskSplitter

        :param name: 节点名称
        :param split_item: 自定义单个子任务处理函数，默认使用恒等映射
        :param stage_mode: 节点运行模式，默认 'serial'
        """
        super().__init__(
            name=name,
            func=self._split,
            stage_mode=stage_mode,
            execution_mode="serial",
            max_retries=0,
        )

        self.split_item = split_item or self._identity_split_item
        self._init_extra_counter()

    def _init_extra_counter(self) -> None:
        """初始化 split 计数器，用于跟踪 split 产生的子任务总数"""
        self.split_counter = ValueWrapper(0, self.metrics.lock)

    def set_execution_mode(self, execution_mode: str) -> None:
        """覆写父类方法，将执行模式固定为串行"""
        super().set_execution_mode("serial")

    def get_binding_counter(self, _downstream_name: str) -> Any:
        """
        返回下游 stage 应绑定的计数器

        :param _downstream_name: 下游 stage 的唯一名称
        :return: split 计数器实例
        """
        return self.split_counter

    def _update_split_counter(self, add_value: int) -> None:
        """
        更新 split 计数器

        :param add_value: 增加的子任务数量
        """
        self.split_counter.add(add_value)

    @staticmethod
    def _identity_split_item(task: TItem) -> RItem:
        """
        默认的单个子任务处理逻辑。

        :param task: 拆分出的单个子任务
        :return: 处理后的单个子任务
        """
        return cast(RItem, task)

    def _split(self, task: Iterable[TItem]) -> Iterable[RItem]:
        """
        将可迭代任务拆分并物化为稳定元组，避免一次性迭代器被重复消费。

        :param task: 任务对象
        :return: 子任务元组
        """
        return (self.split_item(item) for item in task)

    def process_task_success(
        self,
        task_envelope: TaskEnvelope[Iterable[TItem]],
        result: Iterable[RItem],
        start_time: float,
    ) -> None:
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()
        result_list = list(result)

        split_count = self._put_split_result(result_list, task_id)
        self.metrics.add_success_count()
        self.fallback_inlet.task_success(
            task_id, result_list, persist=self.persist_result
        )
        self._update_split_counter(split_count)

        self.log_inlet.split_success(
            self.get_func_name(),
            self._get_task_repr(task),
            split_count,
            time.perf_counter() - start_time,
        )

    def _put_split_result(
        self,
        result: Iterable[RItem],
        task_id: int,
    ) -> int:
        """
        将 split 结果放入队列，并发出对应事件

        :param result: split 的结果，必须是一个可迭代对象
        :param task_id: 原始任务 ID，用于事件关联
        :param task: 原始任务对象
        :return: split 的子任务数量
        """
        result_queue = cast(TaskOutQueue[RItem], self.result_queue)
        result_list = list(result)
        split_count = len(result_list)

        for idx, item in enumerate(result_list):
            split_id = self.ctree_client.emit(
                "task.split",
                parents=[task_id],
                payload=self.get_summary(),
            )
            for target_name in result_queue.target_names:
                downstream_input_id = self.ctree_client.emit(
                    "task.input",
                    parents=[split_id],
                    payload=self.get_summary(),
                )
                self.fallback_inlet.task_in(target_name, downstream_input_id, item)
                downstream_envelope: TaskEnvelope[RItem] = TaskEnvelope(
                    item,
                    downstream_input_id,
                )
                result_queue.put_target(downstream_envelope, target_name)

            self.log_inlet.split_trace(
                self.get_func_name(),
                idx + 1,
                split_count,
                task_id,
                split_id,
            )

        return split_count


# ==== TaskRouter ====
class TaskRouter[T](TaskStage[T, tuple[str, T]]):
    """TaskRouter: 根据路由信息将任务分发到不同的下游 stage。"""

    route_counters: dict[str, ValueWrapper]

    def __init__(
        self, name: str, router: Callable[[T], str], *, stage_mode: str = "serial"
    ):
        """
        初始化 TaskRouter

        :param name: 节点名称
        :param router: 路由函数，根据任务数据返回目标 stage 的唯一名称
        :param stage_mode: 节点运行模式，默认 'serial'
        """
        super().__init__(
            name=name,
            func=self._route,
            stage_mode=stage_mode,
            execution_mode="serial",
            max_retries=0,
        )
        self.router = router

        self._init_extra_counter()

    def _init_extra_counter(self) -> None:
        """
        初始化路由计数器

        每个 target_name 一个计数器，用于让不同下游 stage 的 task_counter 统计正确。
        """
        self.route_counters = {}

    def get_binding_counter(self, downstream_name: str) -> Any:
        """
        返回下游 stage 应绑定的计数器，按唯一名称查找或创建

        :param downstream_name: 下游 stage 的唯一名称
        :return: 对应下游的路由计数器实例
        """
        self.route_counters.setdefault(
            downstream_name, ValueWrapper(0, self.metrics.lock)
        )
        return self.route_counters[downstream_name]

    def _route(self, task: T) -> tuple[str, T]:
        """
        校验路由输入格式并提取目标任务

        :param task: 任务数据
        :return: 提取出的任务数据
        :raises InvalidOptionError: target 不在已注册的路由列表中
        """
        target = self.router(task)

        if target not in self.route_counters:
            raise InvalidOptionError(
                "Unknown target", target, self.route_counters.keys()
            )
        return target, task

    def process_task_success(
        self,
        task_envelope: TaskEnvelope[T],
        result: tuple[str, T],
        start_time: float,
    ) -> None:
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        target, task = result
        task_id = task_envelope.get_id()
        result_queue = cast(TaskOutQueue[T], self.result_queue)

        route_id = self.ctree_client.emit(
            "task.route",
            parents=[task_id],
            payload=self.get_summary(),
        )
        self.metrics.add_success_count()
        self.fallback_inlet.task_success(task_id, task, persist=self.persist_result)
        self._update_route_counter(target)

        self.log_inlet.route_success(
            self.get_func_name(),
            f"({format_repr(task, self.max_info)})",
            target,
            time.perf_counter() - start_time,
            task_id,
            route_id,
        )

        downstream_input_id = self.ctree_client.emit(
            "task.input",
            parents=[route_id],
            payload=self.get_summary(),
        )
        self.fallback_inlet.task_in(target, downstream_input_id, task)
        downstream_envelope: TaskEnvelope[T] = TaskEnvelope(
            task,
            downstream_input_id,
        )
        result_queue.put_target(downstream_envelope, target)

    def _update_route_counter(self, target: str) -> None:
        """
        更新指定目标的路由计数器

        :param target: 目标 stage 的唯一名称
        """
        self.route_counters[target].add(1)
