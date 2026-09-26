"""
Demo: 用 skip 机制实现任务去重。

``skip_func`` 接收单个任务并返回 ``bool``：返回 ``True`` 时该任务不执行 ``func``，
而是直接记为「跳过」。把「该任务是否已经出现过」交给 ``skip_func``，就得到了一种
节点内的去重能力（这也是当初移除内建判重机制后，推荐的替代做法）：

- 单 Executor 场景：直接给 ``TaskExecutor`` 配一个去重判定函数。
- Graph 场景：在图中的某个节点去重，让重复任务不再继续向下游传播。

注意：判定函数由使用方自行保证线程安全（本文件用锁封装），并且任务本身或其派生
key 必须可哈希。
"""

from __future__ import annotations

from collections.abc import Callable
from threading import Lock
from typing import Any

from demo_utils import no_op

from celestialflow import PrintObserver, TaskExecutor, TaskGraph, TaskSplitter


# ==== 去重判定器 ====


class DedupSkipFunc:
    """基于「已见过集合」的去重判定器，可直接作为 ``skip_func`` 使用。

    首次出现的 key 放行（返回 ``False``），再次出现的 key 跳过（返回 ``True``）。
    内部用锁保护「查重 + 登记」，因此在 thread / async 执行模式下也可安全复用。
    """

    def __init__(self, key: Callable[[Any], Any] | None = None) -> None:
        """
        初始化去重判定器。

        :param key: 从任务中提取去重键的函数；默认直接用任务本身作为键
        """
        self._key: Callable[[Any], Any] = key if key is not None else (lambda task: task)
        self._seen: set[Any] = set()
        self._lock = Lock()

    def __call__(self, task: Any) -> bool:
        """
        判断任务是否已经出现过。

        :param task: 待判定的任务
        :return: 已出现过返回 ``True``（跳过），首次出现返回 ``False``（放行）
        """
        key = self._key(task)
        with self._lock:
            if key in self._seen:
                return True
            self._seen.add(key)
            return False


# ==== 场景一：单 Executor ====


def demo_skip_dedup_executor() -> None:
    """
    单 Executor 场景：用 ``skip_func`` 去重。

    输入含重复值的任务列表，``DedupSkipFunc`` 只放行首次出现的任务；被跳过的任务
    既不执行 ``no_op``，也不消耗重试次数。因此 ``tasks_succeeded`` 等于去重后的
    数量，``tasks_skipped`` 等于重复任务数。
    """
    tasks = [1, 2, 3, 1, 2, 1]  # 6 个任务，去重后 3 个，重复 3 个

    executor = TaskExecutor(
        "DedupExecutor",
        no_op,
        execution_mode="thread",
        max_workers=4,
        skip_func=DedupSkipFunc(),
    )
    executor.add_observer(PrintObserver("DedupExecutor"))

    executor.run(tasks)

    counts = executor.metrics.get_counts()
    unique = sorted(task for task, _ in executor.get_success_pairs())
    print(
        f"\n[executor] input={counts['tasks_input']}, "
        f"succeeded={counts['tasks_succeeded']}, "
        f"skipped={counts['tasks_skipped']}"
    )
    print(f"[executor] 去重后保留的任务: {unique}")


# ==== 场景二：Graph ====


def split_with_duplicates(n: int) -> list[dict[str, Any]]:
    """
    把一个任务拆成 3 个子任务，故意让 ``id`` 与相邻子任务重复。

    :param n: 上游任务值
    :return: 含重复 ``id`` 的子任务列表
    """
    return [
        {"id": n, "part": "x"},
        {"id": n, "part": "y"},
        {"id": n + 1, "part": "x"},
    ]


def record_part(task: dict[str, Any]) -> str:
    """
    记录单个子任务。

    :param task: 子任务数据
    :return: 可读的记录字符串
    """
    return f"#{task['id']}:{task['part']}"


def demo_skip_dedup_graph() -> None:
    """
    Graph 场景：在图的中间节点去重。

    ``Generator`` 会把每个任务拆成带重复 ``id`` 的子任务，``Dedup`` 按 ``id`` 去重，
    于是 ``Sink`` 只会收到去重后的子任务：

        Generator --(含重复 id)--> Dedup --(已去重)--> Sink

    ``Dedup`` 的 ``tasks_input`` 是它实际收到的全部子任务数，``tasks_succeeded``
    是其中的唯一 ``id`` 数，``tasks_skipped`` 是被拦截的重复数。

    注意 ``TaskExecutor`` 会把 ``func`` 的返回值下发给下游，因此 ``Dedup`` 用 ``no_op``
    原样透传任务，``Sink`` 收到的仍是子任务字典。
    """
    generator = TaskSplitter(
        "Generator",
        split_with_duplicates,
        execution_mode="thread",
        max_workers=4,
    )
    dedup = TaskExecutor(
        "Dedup",
        no_op,
        execution_mode="thread",
        max_workers=4,
        skip_func=DedupSkipFunc(key=lambda task: task["id"]),
    )
    sink = TaskExecutor(
        "Sink",
        record_part,
        execution_mode="thread",
        max_workers=4,
    )

    graph = TaskGraph("demo_skip_dedup_graph", graph_mode="thread")
    graph.set_nodes(nodes=[generator, dedup, sink])
    graph.connect([generator], [dedup])
    graph.connect([dedup], [sink])

    # 3 个种子任务会被拆成 9 个含重复 id 的子任务，去重后仅剩 4 个流入 Sink。
    graph.run({"Generator": [1, 2, 3]})

    print("\n[graph] 各节点计数:")
    for name in ["Generator", "Dedup", "Sink"]:
        counts = graph.node_dict[name].metrics.get_counts()
        print(
            f"  {name:<10} input={counts['tasks_input']:<4} "
            f"ok={counts['tasks_succeeded']:<4} "
            f"fail={counts['tasks_failed']:<4} "
            f"skip={counts['tasks_skipped']:<4} "
            f"pending={counts['tasks_pending']}"
        )


if __name__ == "__main__":
    demo_skip_dedup_executor()
    demo_skip_dedup_graph()
