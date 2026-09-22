# node/core_nodes.py
import time
from collections.abc import Iterable

from ..persistence import get_lifecycle_inlet, get_log_inlet
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
    - 任务输入/结果队列、metrics 状态与 ctree 客户端由执行器自身持有；全局
      ``LifecycleSpout`` / ``LogSpout`` 由 :func:`funnel_scope` 负责启停，TaskExecutor
      自身不直接持有 spout/inlet 实例。
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

        self.metrics.add_success_count()

        get_lifecycle_inlet().task_success(task_id, result)
        get_log_inlet().task_success(
            self.get_name(),
            self._get_repr(task),
            self._get_repr(result),
            time.perf_counter() - start_perf,
            task_id,
            result_id,
        )

        for target_name in self.yield_queue.get_target_names():
            self.metrics.add_downstream_count(target_name)
            downstream_input_id = self.ctree_client.emit(
                CTreeEvent.TASK_INPUT,
                parents=[result_id],
            )
            get_log_inlet().task_input(
                target_name,
                self._get_repr(result),
                downstream_input_id,
            )
            get_lifecycle_inlet().task_input(target_name, downstream_input_id, result)
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

        self.metrics.add_success_count()

        get_lifecycle_inlet().task_success(task_id, result_list)
        get_log_inlet().task_success(
            self.get_name(),
            self._get_repr(task),
            self._get_repr(result_list),
            time.perf_counter() - start_perf,
            task_id,
            result_id,
        )

        for target_name in self.yield_queue.get_target_names():
            self.metrics.add_downstream_count(target_name, len(result_list))
            for item in result_list:
                downstream_input_id = self.ctree_client.emit(
                    CTreeEvent.TASK_INPUT,
                    parents=[result_id],
                )
                get_lifecycle_inlet().task_input(target_name, downstream_input_id, item)
                get_log_inlet().task_input(
                    target_name,
                    self._get_repr(item),
                    downstream_input_id,
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
        :raises InvalidOptionError: 若路由目标未通过 ``connect_to`` 绑定
        """
        unknown = [t for t in result if t not in self.metrics.downstream_counter]
        if unknown:
            raise InvalidOptionError(
                "Unknown target", unknown[0], self.metrics.downstream_counter.keys()
            )

        task = task_envelope.get_task()
        task_id = task_envelope.get_id()
        result_id = self.ctree_client.emit(
            CTreeEvent.TASK_SUCCESS,
            parents=[task_id],
        )

        self.metrics.add_success_count()

        get_lifecycle_inlet().task_success(task_id, task)
        get_log_inlet().task_success(
            self.get_name(),
            self._get_repr(task),
            self._get_repr(result),
            time.perf_counter() - start_perf,
            task_id,
            result_id,
        )

        for target, yie in result.items():
            self.metrics.add_downstream_count(target)

            downstream_input_id = self.ctree_client.emit(
                CTreeEvent.TASK_INPUT,
                parents=[result_id],
            )
            get_lifecycle_inlet().task_input(target, downstream_input_id, yie)
            get_log_inlet().task_input(
                target,
                self._get_repr(yie),
                downstream_input_id,
            )
            downstream_envelope: TaskEnvelope[Y] = TaskEnvelope(
                yie,
                downstream_input_id,
            )
            self.yield_queue.put_target(target, downstream_envelope)
