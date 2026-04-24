import os

from dotenv import load_dotenv

from demo_utils import (
    add_5,
    add_10,
    add_15,
    add_one_sleep,
    square,
)

from celestialflow import (
    TaskChain,
    TaskComplete,
    TaskCross,
    TaskGraph,
    TaskGrid,
    TaskLoop,
    TaskStage,
    TaskWheel,
)

load_dotenv()

report_host = os.getenv("REPORT_HOST")
report_port = os.getenv("REPORT_PORT")

ctree_host = os.getenv("CTREE_HOST")
ctree_http_host = os.getenv("CTREE_HTTP_PORT")
ctree_grpc_port = os.getenv("CTREE_GRPC_PORT")


# ========有向无环图(DAG)========
def demo_chain():
    # 构建 DAG: A ➝ B ➝ C ➝ D ➝ E
    stageA = TaskStage("StageA", square, execution_mode="serial", max_workers=2)
    stageB = TaskStage("StageB", square, execution_mode="serial", max_workers=2)
    stageC = TaskStage("StageC", square, execution_mode="serial", max_workers=2)
    stageD = TaskStage("StageD", square, execution_mode="serial", max_workers=2)
    stageE = TaskStage("StageE", square, execution_mode="serial", max_workers=2)

    # 设置图结构
    chain = TaskChain([stageA, stageB, stageC, stageD, stageE], "process")
    chain.set_reporter(True, host=report_host, port=report_port)
    chain.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    chain.start_chain(
        {
            stageA.get_tag(): range(20),
        }
    )


def demo_forest():
    # 构建 DAG: A ➝ B ➝ E；C ➝ D ➝ E
    stageA = TaskStage(
        "stageA",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
        stage_mode="process",
    )
    stageB = TaskStage(
        "stageB",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
        stage_mode="process",
    )
    stageC = TaskStage(
        "stageC",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
        stage_mode="process",
    )
    stageD = TaskStage(
        "stageD",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
        stage_mode="process",
    )
    stageE = TaskStage(
        "stageE",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
        stage_mode="process",
    )

    # 构建 DAG: F ➝ G ➝ I；F ➝ H ➝ J
    stageF = TaskStage(
        "stageF",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
        stage_mode="process",
    )
    stageG = TaskStage(
        "stageG",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
        stage_mode="process",
    )
    stageH = TaskStage(
        "stageH",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
        stage_mode="process",
    )
    stageI = TaskStage(
        "stageI",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
        stage_mode="process",
    )
    stageJ = TaskStage(
        "stageJ",
        add_one_sleep,
        execution_mode="thread",
        max_workers=2,
        stage_mode="process",
    )

    # 设置图结构
    graph = TaskGraph()
    graph.set_stages(
        root_stages=[stageA, stageB, stageF],
        stages=[
            stageA,
            stageB,
            stageC,
            stageD,
            stageE,
            stageF,
            stageG,
            stageH,
            stageI,
            stageJ,
        ],
    )
    graph.connect([stageA], [stageC])
    graph.connect([stageB], [stageD])
    graph.connect([stageC], [stageE])
    graph.connect([stageD], [stageE])

    graph.connect([stageF], [stageG, stageH])
    graph.connect([stageG], [stageI])
    graph.connect([stageH], [stageJ])

    graph.set_reporter(True, host=report_host, port=report_port)
    graph.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    # 初始任务
    init_tasks = {
        stageA.get_tag(): range(1, 11),
        stageB.get_tag(): range(11, 21),
        stageF.get_tag(): range(21, 31),
    }

    graph.start_graph(init_tasks)


def demo_cross():
    # 构建 DAG
    stageA = TaskStage("StageA", add_one_sleep, execution_mode="thread", max_workers=2)
    stageB = TaskStage("StageB", add_one_sleep, execution_mode="thread", max_workers=2)
    stageC = TaskStage("StageC", add_one_sleep, execution_mode="thread", max_workers=2)
    stageD = TaskStage("StageD", add_one_sleep, execution_mode="thread", max_workers=5)
    stageE = TaskStage("StageE", add_one_sleep, execution_mode="thread", max_workers=2)
    stageF = TaskStage("StageF", add_one_sleep, execution_mode="thread", max_workers=2)
    stageG = TaskStage("StageG", add_one_sleep, execution_mode="thread", max_workers=2)

    # 构建 TaskCross
    cross = TaskCross(
        [[stageA, stageB, stageC], [stageD], [stageE, stageF, stageG]], "staged"
    )
    cross.set_reporter(True, host=report_host, port=report_port)
    cross.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    # 初始任务
    init_tasks = {
        stageA.get_tag(): range(1, 11),  # random_values(100, "str"),
        stageB.get_tag(): range(6, 16),
        stageC.get_tag(): range(11, 21),
    }

    cross.start_cross(init_tasks)


def demo_network():
    # 输入层
    A1 = TaskStage("A1", add_one_sleep, execution_mode="thread", max_workers=2)
    A2 = TaskStage("A2", add_one_sleep, execution_mode="thread", max_workers=2)

    # 隐藏层
    B1 = TaskStage("B1", add_one_sleep, execution_mode="thread", max_workers=2)
    B2 = TaskStage("B2", add_one_sleep, execution_mode="thread", max_workers=2)
    B3 = TaskStage("B3", add_one_sleep, execution_mode="thread", max_workers=2)

    # 输出层
    C = TaskStage("C", add_one_sleep, execution_mode="thread", max_workers=2)

    # 构建任务图
    cross = TaskCross([[A1, A2], [B1, B2, B3], [C]])
    cross.set_reporter(True, host=report_host, port=report_port)
    cross.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    # 初始任务（输入层）
    init_tasks = {
        A1.get_tag(): range(1, 11),
        A2.get_tag(): range(11, 21),
    }

    cross.start_cross(init_tasks, True)


def demo_star():
    # 定义核心与边节点函数
    core = TaskStage("Core", square)
    side1 = TaskStage("Side1", add_5)
    side2 = TaskStage("Side2", add_10)
    side3 = TaskStage("Side3", add_15)

    # 构造 TaskCross
    star = TaskCross([[core], [side1, side2, side3]], "eager")
    star.set_reporter(True, host=report_host, port=report_port)
    star.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    star.start_cross({core.get_tag(): range(1, 11)})


def demo_fanin():
    # 创建 3 个节点，每个节点有不同偏移
    source1 = TaskStage("Source1", add_5)
    source2 = TaskStage("Source2", add_10)
    source3 = TaskStage("Source3", square)
    merge = TaskStage("Merge", add_one_sleep, execution_mode="thread", max_workers=2)

    # 构造 TaskCross
    fainin = TaskCross([[source1, source2, source3], [merge]], "eager")
    fainin.set_reporter(True, host=report_host, port=report_port)
    fainin.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    fainin.start_cross(
        {
            source1.get_tag(): range(1, 11),
            source2.get_tag(): range(11, 21),
            source3.get_tag(): range(21, 31),
        }
    )


def demo_grid():
    # 1. 构造网格
    grid = [
        [
            TaskStage(
                f"Grid{r}{c}", add_one_sleep, execution_mode="thread", max_workers=2
            )
            for c in range(4)
        ]
        for r in range(4)
    ]

    # 2. 构建 TaskGrid 实例
    task_grid = TaskGrid(grid, "staged")
    task_grid.set_reporter(True, host=report_host, port=report_port)
    task_grid.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    # 3. 初始化任务字典，只放左上角一个任务
    init_dict = {grid[0][0].get_tag(): range(10)}

    # 4. 启动任务图
    task_grid.start_graph(init_dict)


# ========有环图========
def demo_loop():
    stageA = TaskStage("StageA", add_one_sleep, execution_mode="serial")
    stageB = TaskStage("StageB", add_one_sleep, execution_mode="serial")
    stageC = TaskStage("StageC", add_one_sleep, execution_mode="serial")

    loop = TaskLoop([stageA, stageB, stageC])
    loop.set_reporter(True, host=report_host, port=report_port)
    loop.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    # 要测试的任务列表
    test_task_0 = range(1, 2)
    test_task_1 = list(test_task_0) + [0, 6, None, 0, ""]

    loop.start_loop({stageA.get_tag(): test_task_0})


def demo_wheel():
    # 定义核心与边节点函数
    core = TaskStage("Core", square)
    side1 = TaskStage("Side1", add_one_sleep)
    side2 = TaskStage("Side2", add_one_sleep)
    side3 = TaskStage("Side3", add_one_sleep)
    side4 = TaskStage("Side4", add_one_sleep)

    # 构造 TaskCross
    wheel = TaskWheel(core, [side1, side2, side3, side4])
    wheel.set_reporter(True, host=report_host, port=report_port)
    wheel.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    wheel.start_wheel({core.get_tag(): range(1, 11)}, True)


def demo_complete():
    # 创建 3 个节点，每个节点有不同偏移
    n1 = TaskStage("Node1", add_5, execution_mode="thread", max_workers=5)
    n2 = TaskStage("Node2", add_10, execution_mode="thread", max_workers=5)
    n3 = TaskStage("Node3", square, execution_mode="thread", max_workers=5)

    # 构造 TaskComplete
    complete = TaskComplete([n1, n2, n3])
    complete.set_reporter(True, host=report_host, port=report_port)
    complete.set_ctree(
        True, host=ctree_host, http_port=ctree_http_host, grpc_port=ctree_grpc_port
    )

    complete.start_complete(
        {
            n1.get_tag(): range(1, 11),
            n2.get_tag(): range(11, 21),
            n3.get_tag(): range(21, 31),
        }
    )


if __name__ == "__main__":
    demo_loop()
    # demo_cross()
    # demo_grid()
    pass
