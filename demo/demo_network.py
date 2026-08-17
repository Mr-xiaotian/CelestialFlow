# demo/demo_network.py — Step 1: 给每个节点加上权重和偏置
#
# 从一个最小的改动开始：把 add_one_sleep(x) = x + 1
# 换成 y = w * x + b，每个节点有自己的 (w, b)。
#
# 拓扑还是 TaskCross 的 2-3-1 全连接：
#
#   A1 ─┬──→ B1 ─┬──→ C
#       │         │
#   A2 ─┼──→ B2 ─┤
#       │         │
#       └──→ B3 ─┘

from __future__ import annotations

from celestialflow import TaskCross, TaskStage


def linear(w: float, b: float):
    """返回一个线性函数 y = w * x + b。

    ``TaskStage`` 要求 func 只接收一个位置参数，
    这里用闭包把 (w, b) 固定住。
    """

    def _forward(x):
        return w * x + b

    return _forward


def demo_network_step1() -> None:
    """2-3-1 网络，每个节点做 y = w*x + b。"""

    # ── 输入层 ────────────────────────────────────────────────
    # A1 的权重设为 0.5，偏置 0.0 → A1(x) = 0.5 * x
    # A2 的权重设为 2.0，偏置 0.0 → A2(x) = 2.0 * x
    A1 = TaskStage(
        "A1", linear(0.5, 0.0),
        execution_mode="thread", max_workers=2,
    )
    A2 = TaskStage(
        "A2", linear(2.0, 0.0),
        execution_mode="thread", max_workers=2,
    )

    # ── 隐藏层 ────────────────────────────────────────────────
    # 给每个 B 不同的权重，观察 Fan-in 时独立处理的效果
    B1 = TaskStage(
        "B1", linear(1.0, 0.0),
        execution_mode="thread", max_workers=2,
    )
    B2 = TaskStage(
        "B2", linear(1.0, 0.0),
        execution_mode="thread", max_workers=2,
    )
    B3 = TaskStage(
        "B3", linear(1.0, 0.0),
        execution_mode="thread", max_workers=2,
    )

    # ── 输出层 ────────────────────────────────────────────────
    C = TaskStage(
        "C", linear(1.0, 0.0),
        execution_mode="thread", max_workers=2,
        persist_result=True,
    )

    # ── 构建图 ────────────────────────────────────────────────
    cross = TaskCross(
        "demo_network_step1",
        [[A1, A2], [B1, B2, B3], [C]],
        graph_mode="thread",
    )

    # ── 输入数据 ──────────────────────────────────────────────
    # A1 接收 [1, 2, 3, 4, 5]
    # A2 接收 [11, 12, 13, 14, 15]
    # 这些还是独立的任务整数，暂时还没有"样本配对"
    init_tasks = {
        A1.get_name(): [1, 2, 3, 4, 5],
        A2.get_name(): [11, 12, 13, 14, 15],
    }

    print("─── Step 1: 每个节点 y = w*x + b ───\n")
    print(f"  A1(x) = 0.5 * x,  输入: {init_tasks[A1.get_name()]}")
    print(f"  A2(x) = 2.0 * x,  输入: {init_tasks[A2.get_name()]}")
    print("  B1..B3(x) = 1.0 * x")
    print("  C(x) = 1.0 * x")
    print("  运行中...")

    cross.run(init_tasks)

    # ── 收集结果 ──────────────────────────────────────────────
    success_pairs = C.get_success_pairs()
    print(f"  C 共收到 {len(success_pairs)} 个任务\n")
    print("  C 的 (输入 → 输出) 前 10 条:")
    for task, result in success_pairs[:10]:
        print(f"    {task!r:>6}  →  {result!r}")


if __name__ == "__main__":
    demo_network_step1()
