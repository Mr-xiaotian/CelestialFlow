# runtime/util_factories.py
from typing import TYPE_CHECKING, Any

from .core_queue import TaskInQueue, TaskOutQueue

if TYPE_CHECKING:
    from ..stage import TaskExecutor


# ==== 函数工厂 ====
def make_task_in_queue(
    *,
    queue: Any,
    executor: "TaskExecutor",
) -> TaskInQueue:
    """
    创建执行器的输入队列

    :param queue: 队列实例
    :param executor: 执行器实例
    :return: TaskInQueue 实例
    """
    return TaskInQueue(
        queue=queue,
        source_names=[],
        out_name=executor.get_name(),
        log_inlet=executor.log_inlet,
    )


def make_task_out_queue(
    *,
    queue: Any,
    executor: "TaskExecutor",
) -> TaskOutQueue:
    """
    创建执行器的输出队列

    :param queue: 队列实例
    :param executor: 执行器实例
    :return: TaskOutQueue 实例
    """
    return TaskOutQueue(
        queue_list=[queue],
        target_names=[None],
        in_name=executor.get_name(),
        log_inlet=executor.log_inlet,
    )
