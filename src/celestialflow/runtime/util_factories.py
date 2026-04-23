# runtime/util_factories.py
from _thread import LockType
from asyncio import Queue as AsyncQueue
from multiprocessing import Value as MPValue
from queue import Queue as ThreadQueue
from threading import Lock
from typing import TYPE_CHECKING, Any

from .core_queue import TaskInQueue, TaskOutQueue
from .util_types import ValueWrapper

if TYPE_CHECKING:
    from ..stage import TaskExecutor


# ==== 函数工厂 ====
def make_counter(mode: str, *, lock: LockType | None = None, init: int = 0) -> Any:
    """
    返回一个 counter：ValueWrapper(±lock) 或 MPValue

    :param mode: 执行模式
    :param lock: 可选的线程锁（仅 thread 模式使用）
    :param init: 初始值
    :return: 计数器实例
    """
    if mode == "process":
        return MPValue("i", init)

    if mode == "thread":
        return ValueWrapper(init, lock=lock or Lock())

    # serial / async
    return ValueWrapper(init)


def make_queue_backend(mode: str) -> type:
    """
    返回一个”队列类/构造器”，用于创建单通道队列。

    说明：
    - 你当前实现里，process 也用 ThreadQueue（因为节点内使用，不跨进程）。
    - 如果未来需要节点间跨进程通信，把 process 改为 MPQueue 即可。

    :param mode: 执行模式
    :return: 队列类
    """
    if mode == "async":
        return AsyncQueue
    if mode in ("thread", "serial"):
        return ThreadQueue
    return ThreadQueue


def make_task_in_queue(
    *,
    queue: any,
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
        queue_tags=[],
        out_tag=executor.get_tag(),
        log_inlet=executor.log_inlet,
    )


def make_task_out_queue(
    *,
    queue: any,
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
        queue_tags=[None],
        in_tag=executor.get_tag(),
        log_inlet=executor.log_inlet,
    )
