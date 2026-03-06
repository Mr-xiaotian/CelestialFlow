# runtime/factories.py
from asyncio import Queue as AsyncQueue
from queue import Queue as ThreadQueue
from multiprocessing import Value as MPValue
from _thread import LockType
from threading import Lock
from typing import TYPE_CHECKING

from .types import ValueWrapper
from .queue import TaskQueue

if TYPE_CHECKING:
    from ..stage import TaskStage


# ==== 函数工厂 ====
def make_counter(
    mode: str, *, lock: LockType | None = None, init: int = 0
) -> ValueWrapper:
    """
    返回一个 counter：ValueWrapper(±lock) 或 MPValue
    """
    if mode == "process":
        return MPValue("i", init)

    if mode == "thread":
        return ValueWrapper(init, lock=lock or Lock())

    # serial / async
    return ValueWrapper(init)


def make_queue_backend(mode: str):
    """
    返回一个“队列类/构造器”，用于创建单通道队列。

    说明：
    - 你当前实现里，process 也用 ThreadQueue（因为节点内使用，不跨进程）。
    - 如果未来需要节点间跨进程通信，把 process 改为 MPQueue 即可。
    """
    if mode == "async":
        return AsyncQueue
    if mode in ("thread", "serial", "process"):
        return ThreadQueue  # 未来可改为: mode=="process" -> MPQueue
    return ThreadQueue


def make_taskqueue(
    *,
    mode: str,
    direction: str,
    stage: "TaskStage",
):
    Q = make_queue_backend(mode)
    return TaskQueue(
        queue_list=[Q()],
        queue_tags=[None],
        direction=direction,
        stage=stage,
        log_sinker=stage.log_sinker,
        ctree_client=stage.ctree_client,
    )
