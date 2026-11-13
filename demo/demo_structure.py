from demo_utils import (
    add_5,
    add_10,
    add_15,
    add_one_sleep,
    sleep_1,
    square,
)

from celestialflow import (
    TaskChain,
    TaskComplete,
    TaskCross,
    TaskGraph,
    TaskGrid,
    TaskLoop,
    TaskExecutor,
    TaskWheel,
)


# ========有向无环图(DAG)========
def demo_chain() -> None:
    # 构建 DAG: A ➝ B ➝ C ➝ D ➝ E
    node_a = TaskExecutor("NodeA", square, execution_mode="serial", max_workers=2)
    node_b = TaskExecutor("NodeB", square, execution_mode="serial", max_workers=2)
    node_c = TaskExecutor("NodeC", square, execution_mode="serial", max_workers=2)
    node_d = TaskExecutor("NodeD", square, execution_mode="serial", max_workers=2)
    node_e = TaskExecutor("NodeE", square, execution_mode="serial", max_workers=2)

    # 设置图结构
    chain = TaskChain(
        "demo_chain",
        [node_a, node_b, node_c, node_d, node_e],
    )

    chain.run({"NodeA": list(range(20))})


def demo_cross() -> None:
    # 构建 DAG
    node_a = TaskExecutor("NodeA", add_one_sleep, execution_mode="thread", max_workers=2)
    node_b = TaskExecutor("NodeB", add_one_sleep, execution_mode="thread", max_workers=2)
    node_c = TaskExecutor("NodeC", add_one_sleep, execution_mode="thread", max_workers=2)
    node_d = TaskExecutor("NodeD", add_one_sleep, execution_mode="thread", max_workers=5)
    node_e = TaskExecutor("NodeE", add_one_sleep, execution_mode="thread", max_workers=2)
    node_f = TaskExecutor("NodeF", add_one_sleep, execution_mode="thread", max_workers=2)
    node_g = TaskExecutor("NodeG", add_one_sleep, execution_mode="thread", max_workers=2)

    # 构建 TaskCross
    cross = TaskCross(
        "demo_cross",
        [[node_a, node_b, node_c], [node_d], [node_e, node_f, node_g]],
    )

    # 初始任务
    init_tasks = {
        node_a.get_name(): range(1, 11),  # random_values(100, "str"),
        node_b.get_name(): range(6, 16),
        node_c.get_name(): range(11, 21),
    }

    cross.run({name: list(tasks) for name, tasks in init_tasks.items()})


def demo_network() -> None:
    # 输入层
    A1 = TaskExecutor("A1", add_one_sleep, execution_mode="thread", max_workers=2)
    A2 = TaskExecutor("A2", add_one_sleep, execution_mode="thread", max_workers=2)

    # 隐藏层
    B1 = TaskExecutor("B1", add_one_sleep, execution_mode="thread", max_workers=2)
    B2 = TaskExecutor("B2", add_one_sleep, execution_mode="thread", max_workers=2)
    B3 = TaskExecutor("B3", add_one_sleep, execution_mode="thread", max_workers=2)

    # 输出层
    C = TaskExecutor("C", add_one_sleep, execution_mode="thread", max_workers=2)

    # 构建任务图
    cross = TaskCross("demo_network", [[A1, A2], [B1, B2, B3], [C]])

    # 初始任务（输入层）
    init_tasks = {
        A1.get_name(): range(1, 11),
        A2.get_name(): range(11, 21),
    }

    cross.run({name: list(tasks) for name, tasks in init_tasks.items()})


def demo_star() -> None:
    # 定义核心与边节点函数
    core = TaskExecutor("Core", square)
    side1 = TaskExecutor("Side1", add_5)
    side2 = TaskExecutor("Side2", add_10)
    side3 = TaskExecutor("Side3", add_15)

    # 构造 TaskCross
    star = TaskCross(
        "demo_star",
        [[core], [side1, side2, side3]],
    )

    star.run({"Core": list(range(1, 11))})


def demo_fanin() -> None:
    # 创建 3 个节点，每个节点有不同偏移
    source1 = TaskExecutor("Source1", add_5)
    source2 = TaskExecutor("Source2", add_10)
    source3 = TaskExecutor("Source3", square)
    merge = TaskExecutor("Merge", add_one_sleep, execution_mode="thread", max_workers=2)

    # 构造 TaskCross
    fainin = TaskCross(
        "demo_fanin",
        [[source1, source2, source3], [merge]],
    )

    fainin.run(
        {
            "Source1": list(range(1, 11)),
            "Source2": list(range(11, 21)),
            "Source3": list(range(21, 31)),
        }
    )


def demo_grid() -> None:
    # 1. 构造网格
    grid = [
        [
            TaskExecutor(
                f"Grid{r}{c}", add_one_sleep, execution_mode="thread", max_workers=2
            )
            for c in range(4)
        ]
        for r in range(4)
    ]

    # 2. 构建 TaskGrid 实例
    task_grid = TaskGrid("demo_grid", grid)

    # 3. 初始化任务字典，只放左上角一个任务
    init_dict: dict[str, list[int]] = {grid[0][0].get_name(): list(range(10))}

    # 4. 启动任务图
    task_grid.run(init_dict)


# ========有环图========
def demo_loop() -> None:
    # 有环图不会自动终止，任务会持续在环内流转，需要手动 Ctrl+C。
    node_a = TaskExecutor("NodeA", sleep_1, execution_mode="serial")
    node_b = TaskExecutor("NodeB", sleep_1, execution_mode="serial")
    node_c = TaskExecutor("NodeC", sleep_1, execution_mode="serial")

    loop = TaskLoop("demo_loop", [node_a, node_b, node_c])

    # 要测试的任务列表
    test_task_0 = range(10)
    # test_task_1 = list(test_task_0) + [0, 6, None, 0, ""]

    loop.run({"NodeA": list(test_task_0)}, if_put_signal=False)


def demo_wheel() -> None:
    # 有环图不会自动终止，任务会持续在轮环上流转，需要手动 Ctrl+C。
    # 定义核心与边节点函数
    core = TaskExecutor("Core", sleep_1)
    side1 = TaskExecutor("Side1", sleep_1)
    side2 = TaskExecutor("Side2", sleep_1)
    side3 = TaskExecutor("Side3", sleep_1)
    side4 = TaskExecutor("Side4", sleep_1)

    # 构造 TaskCross
    wheel = TaskWheel("demo_wheel", core, [side1, side2, side3, side4])

    wheel.run({"Core": list(range(1, 11))}, if_put_signal=False)


def demo_complete() -> None:
    # 完全图中每个节点都互相连接，任务会持续在全图流转，需要手动 Ctrl+C。
    # 使用不会抛异常的函数，保证图能持续循环。
    n1 = TaskExecutor("Node1", sleep_1, execution_mode="serial", max_workers=5)
    n2 = TaskExecutor("Node2", sleep_1, execution_mode="serial", max_workers=5)
    n3 = TaskExecutor("Node3", sleep_1, execution_mode="serial", max_workers=5)

    # 构造 TaskComplete
    complete = TaskComplete("demo_complete", [n1, n2, n3])

    complete.run(
        {
            "Node1": list(range(1, 11)),
            "Node2": list(range(11, 21)),
            "Node3": list(range(21, 31)),
        }, if_put_signal=False
    )


def demo_multi_cycle() -> None:
    """
    多环互连图:
    分支 A: 2 节点循环 (A1 -> A2 ->  A1)
    分支 B: 2 节点循环 (B1 -> B2 -> B1)
    分支 C: 2 节点循环 (C1 -> C2 -> C1)
    连接: A2 -> B1, A2 -> C1
    """

    # 有环图不会自动终止，任务会持续在多个环之间流转，需要手动 Ctrl+C。
    # 使用不会抛异常的函数，保证图能持续循环。
    # 定义节点
    A1 = TaskExecutor("A1", sleep_1, execution_mode="thread", max_workers=2)
    A2 = TaskExecutor("A2", sleep_1, execution_mode="thread", max_workers=2)

    B1 = TaskExecutor("B1", sleep_1, execution_mode="thread", max_workers=2)
    B2 = TaskExecutor("B2", sleep_1, execution_mode="thread", max_workers=2)

    C1 = TaskExecutor("C1", sleep_1, execution_mode="thread", max_workers=2)
    C2 = TaskExecutor("C2", sleep_1, execution_mode="thread", max_workers=2)

    graph = TaskGraph("demo_multi_cycle", graph_mode="thread")
    graph.set_nodes(
        nodes=[A1, A2, B1, B2, C1, C2],
    )

    # 分支 A 循环
    graph.connect([A1], [A2])
    graph.connect([A2], [A1])

    # A2 引出到 B 和 C
    graph.connect([A2], [B1])
    graph.connect([A2], [C1])

    # 分支 B 循环
    graph.connect([B1], [B2])
    graph.connect([B2], [B1])

    # 分支 C 循环
    graph.connect([C1], [C2])
    graph.connect([C2], [C1])

    graph.run({"A1": list(range(1, 11))}, if_put_signal=False)


if __name__ == "__main__":
    # 前三个为 DAG，会自动结束。
    demo_chain()
    demo_cross()
    demo_grid()
    # 以下为有环图，会持续循环，需要手动 Ctrl+C 终止。
    demo_loop()
    demo_complete()
    demo_multi_cycle()
