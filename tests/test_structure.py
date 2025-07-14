import pytest, logging
import math
from time import sleep
from celestialflow import TaskManager, TaskGraph, TaskLoop, TaskCross, TaskComplete, TaskWheel, TaskGrid


def add_sleep(n):
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

def _test_loop():
    stageA = TaskManager(add_sleep, 'serial')
    stageB = TaskManager(add_sleep, 'serial')
    stageC = TaskManager(add_sleep, 'serial')

    graph = TaskLoop([stageA, stageB, stageC])
    graph.set_reporter(True, host="127.0.0.1", port=5005)

    # 要测试的任务列表
    test_task_0 = range(1, 2)
    test_task_1 = list(test_task_0) + [0, 6, None, 0, '']

    graph.start_loop({
        stageA.get_stage_tag(): test_task_0
    })

def _test_forest():
    # 构建 DAG: A ➝ B ➝ E；C ➝ D ➝ E
    stageA = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageB = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageC = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageD = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageE = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)

    # 构建 DAG: F ➝ G ➝ I；F ➝ H ➝ J
    stageF = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageG = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageH = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageI = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageJ = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)

    # 设置图结构
    stageA.set_graph_context([stageC], stage_mode="process", stage_name="stageA")
    stageB.set_graph_context([stageD], stage_mode="process", stage_name="stageB")
    stageC.set_graph_context([stageE], stage_mode="process", stage_name="stageC")
    stageD.set_graph_context([stageE], stage_mode="process", stage_name="stageD")
    stageE.set_graph_context(stage_mode="process", stage_name="stageE")

    stageF.set_graph_context([stageG, stageH], stage_mode="process", stage_name="stageF")
    stageG.set_graph_context([stageI], stage_mode="process", stage_name="stageG")
    stageH.set_graph_context([stageJ], stage_mode="process", stage_name="stageH")
    stageI.set_graph_context(stage_mode="process", stage_name="stageI")
    stageJ.set_graph_context(stage_mode="process", stage_name="stageJ")

    # 构建 TaskGraph（多根）
    graph = TaskGraph([stageA, stageB, stageF])  # 多根支持
    graph.set_reporter(True, host="127.0.0.1", port=5005)

    # 初始任务
    init_tasks = {
        stageA.get_stage_tag(): range(1, 11),
        stageB.get_stage_tag(): range(11, 21),
        stageF.get_stage_tag(): range(21, 31),
    }

    graph.start_graph(init_tasks)

def test_cross():
    # 构建 DAG
    stageA = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageB = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageC = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageD = TaskManager(add_sleep, execution_mode="thread", worker_limit=5)
    stageE = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageF = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageG = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)

    # 构建 TaskCross
    cross = TaskCross([[stageA, stageB, stageC], [stageD], [stageE, stageF, stageG]], "serial")  # 多根支持
    cross.set_reporter(True, host="127.0.0.1", port=5005)

    # 初始任务
    init_tasks = {
        stageA.get_stage_tag(): range(1, 11),
        stageB.get_stage_tag(): range(6, 16),
        stageC.get_stage_tag(): range(11, 21),
    }

    cross.start_cross(init_tasks)

def test_network():
    # 输入层
    A1 = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    A2 = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    
    # 隐藏层
    B1 = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    B2 = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    B3 = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    
    # 输出层
    C = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)

    # 构建任务图
    cross = TaskCross([[A1, A2], [B1, B2, B3], [C]])
    cross.set_reporter(True, host="127.0.0.1", port=5005)

    # 初始任务（输入层）
    init_tasks = {
        A1.get_stage_tag(): range(1, 11),
        A2.get_stage_tag(): range(11, 21),
    }

    cross.start_cross(init_tasks)

def _test_star():
    # 定义核心与边节点函数
    core = TaskManager(func=square)
    side1 = TaskManager(func=add_5)
    side2 = TaskManager(func=add_10)
    side3 = TaskManager(func=add_15)

    # 构造 TaskCross
    star = TaskCross([[core], [side1, side2, side3]], "process")
    star.set_reporter(True, host="127.0.0.1", port=5005)

    star.start_cross({
        core.get_stage_tag(): range(1,11)
    })

def _test_fanin():
    # 创建 3 个节点，每个节点有不同偏移
    source1 = TaskManager(func=add_5)
    source2 = TaskManager(func=add_10)
    source3 = TaskManager(func=square)
    merge = TaskManager(add_sleep, "thread", 2)

    # 构造 TaskCross
    fainin = TaskCross([[source1, source2, source3], [merge]], "process")
    fainin.set_reporter(True, host="127.0.0.1", port=5005)

    fainin.start_cross({
        source1.get_stage_tag(): range(1, 11),
        source2.get_stage_tag(): range(11, 21),
        source3.get_stage_tag(): range(21, 31),
    })

def _test_wheel():
    # 定义核心与边节点函数
    core = TaskManager(func=square)
    side1 = TaskManager(func=add_sleep)
    side2 = TaskManager(func=add_sleep)
    side3 = TaskManager(func=add_sleep)
    side4 = TaskManager(func=add_sleep)

    # 构造 TaskCross
    wheel = TaskWheel(core, [side1, side2, side3, side4])
    wheel.set_reporter(True, host="127.0.0.1", port=5005)

    wheel.start_wheel({
        core.get_stage_tag(): range(1,11)
    })

def _test_grid():
    # 1. 构造网格
    grid = [
        [TaskManager(add_sleep, "thread", 2) for _ in range(4)]
        for _ in range(4)
    ]

    # 2. 构建 TaskGrid 实例
    task_grid = TaskGrid(grid, "serial")
    task_grid.set_reporter(True, host="127.0.0.1", port=5005)

    # 3. 初始化任务字典，只放左上角一个任务
    init_dict = {
        grid[0][0].get_stage_tag(): range(10)
    }

    # 4. 启动任务图
    task_grid.start_graph(init_dict)

def _test_neural_net_1():
    # 输入层
    A1 = TaskManager(neuron_activation, execution_mode="thread", worker_limit=2)
    A2 = TaskManager(neuron_activation, execution_mode="thread", worker_limit=2)

    # 隐藏层1
    B1 = TaskManager(neuron_activation, execution_mode="thread", worker_limit=2)
    B2 = TaskManager(neuron_activation, execution_mode="thread", worker_limit=2)

    # 隐藏层2
    C1 = TaskManager(neuron_activation, execution_mode="thread", worker_limit=2)

    # 输出层
    D1 = TaskManager(neuron_activation, execution_mode="thread", worker_limit=2)
    D2 = TaskManager(neuron_activation, execution_mode="thread", worker_limit=2)

    # 构建拓扑结构（残差连接 A2 ➝ C1）
    A1.set_graph_context([B1], stage_mode="process", stage_name="A1")
    A2.set_graph_context([B2, C1], stage_mode="process", stage_name="A2")

    B1.set_graph_context([C1], stage_mode="process", stage_name="B1")
    B2.set_graph_context([C1], stage_mode="process", stage_name="B2")

    C1.set_graph_context([D1, D2], stage_mode="process", stage_name="C1")

    D1.set_graph_context(stage_mode="process", stage_name="D1")
    D2.set_graph_context(stage_mode="process", stage_name="D2")

    # 构建任务图
    graph = TaskGraph([A1, A2])
    graph.set_reporter(True, host="127.0.0.1", port=5005)

    # 初始任务输入
    init_tasks = {
        A1.get_stage_tag(): [0.1, 0.5, 0.9],
        A2.get_stage_tag(): [1.1, 1.5, 2.0],
    }

    graph.start_graph(init_tasks)

def _test_complete():
    # 创建 3 个节点，每个节点有不同偏移
    n1 = TaskManager(func=add_5)
    n2 = TaskManager(func=add_10)
    n3 = TaskManager(func=square)

    # 构造 TaskComplete
    complete = TaskComplete([n1, n2, n3])
    complete.set_reporter(True, host="127.0.0.1", port=5005)

    complete.start_complete({
        n1.get_stage_tag(): range(1, 11),
        n2.get_stage_tag(): range(11, 21),
        n3.get_stage_tag(): range(21, 31),
    })


if __name__ == "__main__":
    # test_cross()
    # test_grid()
    pass