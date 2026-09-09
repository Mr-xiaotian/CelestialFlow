import os

from celestialtree import Client as CelestialTreeClient
from demo_utils import (
    add_5,
    add_10,
    add_15,
    add_one_sleep,
    square,
)
from dotenv import load_dotenv

from celestialflow import (
    TaskChain,
    TaskComplete,
    TaskCross,
    TaskGraph,
    TaskGrid,
    TaskLoop,
    TaskReporter,
    TaskExecutor,
    TaskWheel,
)

load_dotenv()

report_host: str = os.getenv("REPORT_HOST", "")
report_port: int = int(os.getenv("REPORT_PORT", "0"))

ctree_host: str = os.getenv("CTREE_HOST", "")
ctree_http_port: int = int(os.getenv("CTREE_HTTP_PORT", "0"))
ctree_grpc_port: int = int(os.getenv("CTREE_GRPC_PORT", "0"))

ctree_client = CelestialTreeClient(
    host=ctree_host,
    http_port=ctree_http_port,
    grpc_port=ctree_grpc_port,
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
    chain.set_reporter(TaskReporter(report_host, report_port, chain))
    # chain.set_ctree(ctree_client)

    chain.run({"NodeA": list(range(20))}, if_put_signal=False)


def demo_forest() -> None:
    # 构建 DAG: A ➝ B ➝ E；C ➝ D ➝ E
    node_a = TaskExecutor(
        "node_a",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_b = TaskExecutor(
        "node_b",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_c = TaskExecutor(
        "node_c",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_d = TaskExecutor(
        "node_d",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_e = TaskExecutor(
        "node_e",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )

    # 构建 DAG: F ➝ G ➝ I；F ➝ H ➝ J
    node_f = TaskExecutor(
        "node_f",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_g = TaskExecutor(
        "node_g",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_h = TaskExecutor(
        "node_h",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_i = TaskExecutor(
        "node_i",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )
    node_j = TaskExecutor(
        "node_j",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
    )

    # 设置图结构
    graph = TaskGraph("demo_forest", graph_mode="thread")
    graph.set_nodes(
        nodes=[
            node_a,
            node_b,
            node_c,
            node_d,
            node_e,
            node_f,
            node_g,
            node_h,
            node_i,
            node_j,
        ],
    )
    graph.connect([node_a], [node_c])
    graph.connect([node_b], [node_d])
    graph.connect([node_c], [node_e])
    graph.connect([node_d], [node_e])

    graph.connect([node_f], [node_g, node_h])
    graph.connect([node_g], [node_i])
    graph.connect([node_h], [node_j])

    graph.set_reporter(TaskReporter(report_host, report_port, graph))
    # graph.set_ctree(ctree_client)

    # 初始任务
    init_tasks: dict[str, list[int]] = {
        node_a.get_name(): list(range(1, 11)),
        node_b.get_name(): list(range(11, 21)),
        node_f.get_name(): list(range(21, 31)),
    }

    graph.run(init_tasks)


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
    cross.set_reporter(TaskReporter(report_host, report_port, cross))
    # cross.set_ctree(ctree_client)

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
    cross.set_reporter(TaskReporter(report_host, report_port, cross))
    # cross.set_ctree(ctree_client)

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
    star.set_reporter(TaskReporter(report_host, report_port, star))
    # star.set_ctree(ctree_client)

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
    fainin.set_reporter(TaskReporter(report_host, report_port, fainin))
    # fainin.set_ctree(ctree_client)

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
    task_grid.set_reporter(TaskReporter(report_host, report_port, task_grid))
    # task_grid.set_ctree(ctree_client)

    # 3. 初始化任务字典，只放左上角一个任务
    init_dict: dict[str, list[int]] = {grid[0][0].get_name(): list(range(10))}

    # 4. 启动任务图
    task_grid.run(init_dict)


# ========有环图========
def demo_loop() -> None:
    node_a = TaskExecutor("NodeA", add_one_sleep, execution_mode="serial")
    node_b = TaskExecutor("NodeB", add_one_sleep, execution_mode="serial")
    node_c = TaskExecutor("NodeC", add_one_sleep, execution_mode="serial")

    loop = TaskLoop("demo_loop", [node_a, node_b, node_c])
    loop.set_reporter(TaskReporter(report_host, report_port, loop))
    # loop.set_ctree(ctree_client)

    # 要测试的任务列表
    test_task_0 = range(10)
    # test_task_1 = list(test_task_0) + [0, 6, None, 0, ""]

    loop.run({"NodeA": list(test_task_0)}, if_put_signal=False)


def demo_wheel() -> None:
    # 定义核心与边节点函数
    core = TaskExecutor("Core", square)
    side1 = TaskExecutor("Side1", add_one_sleep)
    side2 = TaskExecutor("Side2", add_one_sleep)
    side3 = TaskExecutor("Side3", add_one_sleep)
    side4 = TaskExecutor("Side4", add_one_sleep)

    # 构造 TaskCross
    wheel = TaskWheel("demo_wheel", core, [side1, side2, side3, side4])
    wheel.set_reporter(TaskReporter(report_host, report_port, wheel))
    # wheel.set_ctree(ctree_client)

    wheel.run({"Core": list(range(1, 11))}, if_put_signal=False)


def demo_complete() -> None:
    # 创建 3 个节点，每个节点有不同偏移
    n1 = TaskExecutor("Node1", add_5, execution_mode="serial", max_workers=5)
    n2 = TaskExecutor("Node2", add_10, execution_mode="serial", max_workers=5)
    n3 = TaskExecutor("Node3", square, execution_mode="serial", max_workers=5)

    # 构造 TaskComplete
    complete = TaskComplete("demo_complete", [n1, n2, n3])
    complete.set_reporter(TaskReporter(report_host, report_port, complete))
    # complete.set_ctree(ctree_client)

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

    # 定义节点
    A1 = TaskExecutor(
        "A1", add_one_sleep, execution_mode="thread", max_workers=2
    )
    A2 = TaskExecutor(
        "A2", add_one_sleep, execution_mode="thread", max_workers=2
    )

    B1 = TaskExecutor(
        "B1", add_one_sleep, execution_mode="thread", max_workers=2
    )
    B2 = TaskExecutor(
        "B2", add_one_sleep, execution_mode="thread", max_workers=2
    )

    C1 = TaskExecutor(
        "C1", add_one_sleep, execution_mode="thread", max_workers=2
    )
    C2 = TaskExecutor(
        "C2", add_one_sleep, execution_mode="thread", max_workers=2
    )

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

    graph.set_reporter(TaskReporter(report_host, report_port, graph))
    # graph.set_ctree(ctree_client)

    graph.run({"A1": list(range(1, 11))}, if_put_signal=False)


if __name__ == "__main__":
    demo_chain()
    # demo_forest()
    # demo_cross()
    # demo_grid()
    # demo_loop()
    # demo_complete()
    # demo_multi_cycle()
    pass
