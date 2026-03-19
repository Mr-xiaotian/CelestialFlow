# runtime/util_tools.py
from multiprocessing import Queue as MPQueue


# ======== queue处理 ========
def cleanup_mpqueue(queue: MPQueue) -> None:
    """
    清理队列，关闭队列并等待后台线程终止。

    :param queue: 要清理的多进程队列对象
    """
    queue.close()
    queue.join_thread()  # 确保队列的后台线程正确终止
