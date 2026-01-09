import pytest, logging, os
import math
from time import sleep
from dotenv import load_dotenv

from celestialflow import (
    TaskStage,
    TaskGraph,
    TaskChain,
    TaskLoop,
    TaskCross,
    TaskComplete,
    TaskWheel,
    TaskGrid,
)


load_dotenv()
report_host = os.getenv("REPORT_HOST")
report_port = os.getenv("REPORT_PORT")

ctree_host = os.getenv("CTREE_HOST")
ctree_port = os.getenv("CTREE_PORT")


def operate_sleep(a, b):
    sleep(1)
    return a + b, a * b


def operate_sleep_A(a, b):
    return operate_sleep(a, b)


def operate_sleep_B(a, b):
    return operate_sleep(a, b)


def operate_sleep_C(a, b):
    return operate_sleep(a, b)


def operate_sleep_D(a, b):
    return operate_sleep(a, b)


def operate_sleep_E(a, b):
    return operate_sleep(a, b)


def add_one_sleep(n):
    sleep(1)
    if n > 30:
        raise ValueError("Test error for greater than 30")
    elif n == 0:
        raise ValueError("Test error for 0")
    elif n == None:
        raise ValueError("Test error for None")
    return n + 1


def neuron_activation(x):
    if not isinstance(x, (int, float)):
        raise ValueError("Invalid input type")
    sleep(1)  # 模拟计算延迟
    return 1 / (1 + math.exp(-x))  # sigmoid 激活函数


def square(x):
    sleep(1)
    return x * x


def add_offset(x, offset=10):
    if x > 30:
        raise ValueError("Test error for greater than 30")
    sleep(1)
    return x + offset


# 创建带偏移的函数
def add_5(x):
    return add_offset(x, 5)


def add_10(x):
    return add_offset(x, 10)


def add_15(x):
    return add_offset(x, 15)


def add_20(x):
    return add_offset(x, 20)


def add_25(x):
    return add_offset(x, 25)


# ========有向无环图(DAG)========
def test_chain():
    # 构建 DAG: A ➝ B ➝ C ➝ D ➝ E
    stageA = TaskStage(
        operate_sleep_A, execution_mode="serial", worker_limit=2, unpack_task_args=True
    )
    stageB = TaskStage(
        operate_sleep_B, execution_mode="serial", worker_limit=2, unpack_task_args=True
    )
    stageC = TaskStage(
        operate_sleep_C, execution_mode="serial", worker_limit=2, unpack_task_args=True
    )
    stageD = TaskStage(
        operate_sleep_D, execution_mode="serial", worker_limit=2, unpack_task_args=True
    )
    stageE = TaskStage(
        operate_sleep_E, execution_mode="serial", worker_limit=2, unpack_task_args=True
    )

    # 设置图结构
    chain = TaskChain([stageA, stageB, stageC, stageD, stageE], "process")
    chain.set_reporter(True, host=report_host, port=report_port)

    chain.start_chain(
        {
            stageA.get_tag(): [
                (0, 6),
                (3, 7),
                (6, 8),
                (9, 12),
                (12, 16),
                (15, 25),
                (18, 26),
                (21, 29),
                (24, 30),
                (27, 32),
            ],
        }
    )


def test_forest():
    # 构建 DAG: A ➝ B ➝ E；C ➝ D ➝ E
    stageA = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageB = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageC = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageD = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageE = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)

    # 构建 DAG: F ➝ G ➝ I；F ➝ H ➝ J
    stageF = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageG = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageH = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageI = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageJ = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)

    # 设置图结构
    stageA.set_graph_context([stageC], stage_mode="process", stage_name="stageA")
    stageB.set_graph_context([stageD], stage_mode="process", stage_name="stageB")
    stageC.set_graph_context([stageE], stage_mode="process", stage_name="stageC")
    stageD.set_graph_context([stageE], stage_mode="process", stage_name="stageD")
    stageE.set_graph_context(stage_mode="process", stage_name="stageE")

    stageF.set_graph_context(
        [stageG, stageH], stage_mode="process", stage_name="stageF"
    )
    stageG.set_graph_context([stageI], stage_mode="process", stage_name="stageG")
    stageH.set_graph_context([stageJ], stage_mode="process", stage_name="stageH")
    stageI.set_graph_context(stage_mode="process", stage_name="stageI")
    stageJ.set_graph_context(stage_mode="process", stage_name="stageJ")

    # 构建 TaskGraph（多根）
    graph = TaskGraph([stageA, stageB, stageF])  # 多根支持
    graph.set_reporter(True, host=report_host, port=report_port)

    # 初始任务
    init_tasks = {
        stageA.get_tag(): range(1, 11),
        stageB.get_tag(): range(11, 21),
        stageF.get_tag(): range(21, 31),
    }

    graph.start_graph(init_tasks)


def test_cross():
    # 构建 DAG
    stageA = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageB = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageC = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageD = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=5)
    stageE = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageF = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    stageG = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)

    # 构建 TaskCross
    cross = TaskCross(
        [[stageA, stageB, stageC], [stageD], [stageE, stageF, stageG]], "serial"
    )
    cross.set_reporter(True, host=report_host, port=report_port)

    # 初始任务
    init_tasks = {
        stageA.get_tag(): range(1, 11),  # random_values(100, "str"),
        stageB.get_tag(): range(6, 16),
        stageC.get_tag(): range(11, 21),
    }

    cross.start_cross(init_tasks)


def test_network():
    # 输入层
    A1 = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    A2 = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)

    # 隐藏层
    B1 = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    B2 = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)
    B3 = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)

    # 输出层
    C = TaskStage(add_one_sleep, execution_mode="thread", worker_limit=2)

    # 构建任务图
    cross = TaskCross([[A1, A2], [B1, B2, B3], [C]])
    cross.set_reporter(True, host=report_host, port=report_port)

    # 初始任务（输入层）
    init_tasks = {
        A1.get_tag(): range(1, 11),
        A2.get_tag(): range(11, 21),
    }

    cross.start_cross(init_tasks, True)


def test_star():
    # 定义核心与边节点函数
    core = TaskStage(func=square)
    side1 = TaskStage(func=add_5)
    side2 = TaskStage(func=add_10)
    side3 = TaskStage(func=add_15)

    # 构造 TaskCross
    star = TaskCross([[core], [side1, side2, side3]], "process")
    star.set_reporter(True, host=report_host, port=report_port)

    star.start_cross({core.get_tag(): range(1, 11)})


def test_fanin():
    # 创建 3 个节点，每个节点有不同偏移
    source1 = TaskStage(func=add_5)
    source2 = TaskStage(func=add_10)
    source3 = TaskStage(func=square)
    merge = TaskStage(add_one_sleep, "thread", 2)

    # 构造 TaskCross
    fainin = TaskCross([[source1, source2, source3], [merge]], "process")
    fainin.set_reporter(True, host=report_host, port=report_port)

    fainin.start_cross(
        {
            source1.get_tag(): range(1, 11),
            source2.get_tag(): range(11, 21),
            source3.get_tag(): range(21, 31),
        }
    )


def test_grid():
    # 1. 构造网格
    grid = [[TaskStage(add_one_sleep, "thread", 2) for _ in range(4)] for _ in range(4)]

    # 2. 构建 TaskGrid 实例
    task_grid = TaskGrid(grid, "serial")
    task_grid.set_reporter(True, host=report_host, port=report_port)

    # 3. 初始化任务字典，只放左上角一个任务
    init_dict = {grid[0][0].get_tag(): range(10)}

    # 4. 启动任务图
    task_grid.start_graph(init_dict)


# ========有环图========
def test_loop():
    stageA = TaskStage(add_one_sleep, "serial")
    stageB = TaskStage(add_one_sleep, "serial")
    stageC = TaskStage(add_one_sleep, "serial")

    loop = TaskLoop([stageA, stageB, stageC])
    loop.set_reporter(True, host=report_host, port=report_port)
    loop.set_ctree(True, host=ctree_host, port=ctree_port)

    # 要测试的任务列表
    test_task_0 = range(1, 2)
    test_task_1 = list(test_task_0) + [0, 6, None, 0, ""]

    loop.start_loop({stageA.get_tag(): test_task_0})


def test_wheel():
    # 定义核心与边节点函数
    core = TaskStage(func=square)
    side1 = TaskStage(func=add_one_sleep)
    side2 = TaskStage(func=add_one_sleep)
    side3 = TaskStage(func=add_one_sleep)
    side4 = TaskStage(func=add_one_sleep)

    # 构造 TaskCross
    wheel = TaskWheel(core, [side1, side2, side3, side4])
    wheel.set_reporter(True, host=report_host, port=report_port)

    wheel.start_wheel({core.get_tag(): range(1, 11)}, True)


def test_complete():
    # 创建 3 个节点，每个节点有不同偏移
    n1 = TaskStage(func=add_5, execution_mode="thread", worker_limit=5)
    n2 = TaskStage(func=add_10, execution_mode="thread", worker_limit=5)
    n3 = TaskStage(func=square, execution_mode="thread", worker_limit=5)

    # 构造 TaskComplete
    complete = TaskComplete([n1, n2, n3])
    complete.set_reporter(True, host=report_host, port=report_port)

    complete.start_complete(
        {
            n1.get_tag(): range(1, 11),
            n2.get_tag(): range(11, 21),
            n3.get_tag(): range(21, 31),
        }
    )


if __name__ == "__main__":
    test_loop()
    # test_cross()
    # test_grid()
    pass
