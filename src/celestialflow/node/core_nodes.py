# node/core_nodes.py
import time
from collections.abc import Iterable

from ..observer import TaskInputEvent, TaskSuccessEvent
from ..runtime import TaskEnvelope
from ..runtime.util_errors import InvalidOptionError
from ..runtime.util_types import CTreeEvent
from .core_node import BaseTaskNode


# ==== 任务执行器 ====
class TaskExecutor[T, R](BaseTaskNode[T, R, R]):
    """任务执行器基类，支持串行、线程和异步三种执行模式。

    注意：
    - ``start()`` / ``start_async()`` 为一次性调用；启动并运行完成后，不保证当前实例可被
      安全重置并再次复用。如需重复执行同一逻辑，请重新创建新的 TaskExecutor 实例。
    - 启动前的 setter（``set_execution_mode`` / ``set_retry_exceptions`` / ``set_ctree`` /
      ``add_observer`` 等）允许在 start 之前多次调用。
    - 任务输入/结果队列与 ctree 客户端由执行器自身持有；指标由
      :class:`~celestialflow.reporter.core_metrics.MetricsObserver` 依据事件维护：
      独立运行时由 :meth:`~celestialflow.node.core_node.BaseTaskNode.run` 注册单节点
      观察者，参与图调度时由图级观察者统一维护。全局 ``LifecycleSpout`` /
      ``LogSpout`` 的启停与全局 funnel 观察者的注册由
      :meth:`~celestialflow.node.core_node.BaseTaskNode.run` 统一负责，TaskExecutor
      自身不直接持有 spout 实例。
    """

    # ==== 覆写方法 ====

    def process_task_success(
        self, task_envelope: TaskEnvelope[T], result: R, start_perf: float
    ) -> None:
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        result_id = self.ctree_client.emit(
            CTreeEvent.TASK_SUCCESS,
            parents=[task_id],
        )

        task_repr = self._get_repr(task)
        result_repr = self._get_repr(result)
        elapsed = time.perf_counter() - start_perf
        self.observers.on_task_success(
            TaskSuccessEvent(
                node=self.get_name(),
                task=task,
                task_repr=task_repr,
                result=result,
                result_repr=result_repr,
                elapsed=elapsed,
                task_id=task_id,
                success_id=result_id,
            )
        )

        for target_name in self.yield_queue.get_target_names():
            downstream_input_id = self.ctree_client.emit(
                CTreeEvent.TASK_INPUT,
                parents=[result_id],
            )
            self.observers.on_task_input(
                TaskInputEvent(
                    node=target_name,
                    task=task,
                    task_repr=task_repr,
                    input_id=downstream_input_id,
                    source="upstream",
                    from_node=self.get_name(),
                )
            )
            downstream_envelope: TaskEnvelope[R] = TaskEnvelope(
                task=result,
                id=downstream_input_id,
            )
            self.yield_queue.put_target(target_name, downstream_envelope)


# ==== 任务拆分器 ====
class TaskSplitter[T, RItem](BaseTaskNode[T, Iterable[RItem], RItem]):
    """TaskSplitter: 将单个任务拆分为多个子任务，注入下游队列。

    ``func`` 接收单个任务并返回可迭代的子任务序列，子任务将逐个注入下游队列。
    """

    # === 覆写方法 ===

    def process_task_success(
        self,
        task_envelope: TaskEnvelope[T],
        result: Iterable[RItem],
        start_perf: float,
    ) -> None:
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_perf: 任务开始时间
        """
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()
        result_list = list(result)
        result_id = self.ctree_client.emit(
            CTreeEvent.TASK_SUCCESS,
            parents=[task_id],
        )

        task_repr = self._get_repr(task)
        result_repr = self._get_repr(result_list)
        elapsed = time.perf_counter() - start_perf
        self.observers.on_task_success(
            TaskSuccessEvent(
                node=self.get_name(),
                task=task,
                task_repr=task_repr,
                result=result_list,
                result_repr=result_repr,
                elapsed=elapsed,
                task_id=task_id,
                success_id=result_id,
            )
        )

        for target_name in self.yield_queue.get_target_names():
            for item in result_list:
                downstream_input_id = self.ctree_client.emit(
                    CTreeEvent.TASK_INPUT,
                    parents=[result_id],
                )
                item_repr = self._get_repr(item)
                self.observers.on_task_input(
                    TaskInputEvent(
                        node=target_name,
                        task=item,
                        task_repr=item_repr,
                        input_id=downstream_input_id,
                        source="upstream",
                        from_node=self.get_name(),
                    )
                )
                downstream_envelope: TaskEnvelope[RItem] = TaskEnvelope(
                    item,
                    downstream_input_id,
                )
                self.yield_queue.put_target(target_name, downstream_envelope)


# ==== 任务路由器 ====
class TaskRouter[T, Y](BaseTaskNode[T, dict[str, Y], Y]):
    """TaskRouter: 根据路由信息将任务分发到不同的下游节点。"""

    # === 覆写方法 ===

    def process_task_success(
        self,
        task_envelope: TaskEnvelope[T],
        result: dict[str, Y],
        start_perf: float,
    ) -> None:
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_perf: 任务开始时间
        """
        known_targets = tuple(self.yield_queue.get_target_names())
        unknown = [t for t in result if t not in known_targets]
        if unknown:
            raise InvalidOptionError("Unknown target", unknown[0], known_targets)

        task = task_envelope.get_task()
        task_id = task_envelope.get_id()
        result_id = self.ctree_client.emit(
            CTreeEvent.TASK_SUCCESS,
            parents=[task_id],
        )

        task_repr = self._get_repr(task)
        result_repr = self._get_repr(result)
        elapsed = time.perf_counter() - start_perf
        self.observers.on_task_success(
            TaskSuccessEvent(
                node=self.get_name(),
                task=task,
                task_repr=task_repr,
                result=result,
                result_repr=result_repr,
                elapsed=elapsed,
                task_id=task_id,
                success_id=result_id,
            )
        )

        for target, yie in result.items():
            downstream_input_id = self.ctree_client.emit(
                CTreeEvent.TASK_INPUT,
                parents=[result_id],
            )
            yie_repr = self._get_repr(yie)
            self.observers.on_task_input(
                TaskInputEvent(
                    node=target,
                    task=yie,
                    task_repr=yie_repr,
                    input_id=downstream_input_id,
                    source="upstream",
                    from_node=self.get_name(),
                )
            )
            downstream_envelope: TaskEnvelope[Y] = TaskEnvelope(
                yie,
                downstream_input_id,
            )
            self.yield_queue.put_target(target, downstream_envelope)
