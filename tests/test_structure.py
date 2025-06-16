import pytest, logging
import math
from time import sleep
from celestialflow import TaskManager, TaskTree, TaskLoop, TaskStar, TaskFanIn, TaskCross, TaskComplete


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
    stageA = TaskManager(add_sleep, 'thread', 3)
    stageB = TaskManager(add_sleep, 'thread', 3)
    stageC = TaskManager(add_sleep, 'thread', 3)

    tree = TaskLoop([stageA, stageB, stageC])
    tree.set_reporter(True, host="127.0.0.1", port=5005)

    # 要测试的任务列表
    test_task_0 = range(1, 2)
    test_task_1 = list(test_task_0) + [0, 6, None, 0, '']

    tree.start_loop({
        stageA.get_stage_tag(): test_task_0
    })

def _test_forest_0():
    # 构建 DAG: A ➝ B ➝ E；C ➝ D ➝ E
    stageA = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageB = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageC = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageD = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageE = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)

    # 设置图结构
    stageA.set_tree_context(next_stages=[stageC], stage_mode="process", stage_name="A")
    stageB.set_tree_context(next_stages=[stageD], stage_mode="process", stage_name="B")
    stageC.set_tree_context(next_stages=[stageE], stage_mode="process", stage_name="C")
    stageD.set_tree_context(next_stages=[stageE], stage_mode="process", stage_name="D")
    stageE.set_tree_context(stage_mode="process", stage_name="E")

    # 构建 TaskTree（多根）
    tree = TaskTree([stageA, stageB])  # 多根支持
    tree.set_reporter(True, host="127.0.0.1", port=5005)

    # 初始任务
    init_tasks = {
        stageA.get_stage_tag(): range(1, 11),
        stageB.get_stage_tag(): range(11,21)
    }

    tree.start_tree(init_tasks)

def _test_forest_1():
    # 构建 DAG
    stageA = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageB = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageC = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageD = TaskManager(add_sleep, execution_mode="serial", worker_limit=2)
    stageE = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageF = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    stageG = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)

    # 设置图结构
    stageA.set_tree_context(next_stages=[stageD], stage_mode="process", stage_name="A")
    stageB.set_tree_context(next_stages=[stageD], stage_mode="process", stage_name="B")
    stageC.set_tree_context(next_stages=[stageD], stage_mode="process", stage_name="C")
    stageD.set_tree_context(next_stages=[stageE, stageF, stageG], stage_mode="process", stage_name="D")
    stageE.set_tree_context(next_stages=[], stage_mode="process", stage_name="E")
    stageF.set_tree_context(next_stages=[], stage_mode="process", stage_name="F")
    stageG.set_tree_context(next_stages=[], stage_mode="process", stage_name="G")

    # 构建 TaskTree（多根）
    tree = TaskTree([stageA, stageB, stageC])  # 多根支持
    tree.set_reporter(True, host="127.0.0.1", port=5005)

    # 初始任务
    init_tasks = {
        stageA.get_stage_tag(): range(1, 11),
        stageB.get_stage_tag(): range(6, 16),
        stageC.get_stage_tag(): range(11, 21),
    }

    tree.start_tree(init_tasks)

def _test_neural_net_0():
    # 输入层
    A1 = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    A2 = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    
    # 隐藏层
    B1 = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    B2 = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    B3 = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
    
    # 输出层
    C = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)

    # 设置连接关系（像神经网络中的全连接）
    A1.set_tree_context(next_stages=[B1, B2, B3], stage_mode="process", stage_name="A1")
    A2.set_tree_context(next_stages=[B1, B2, B3], stage_mode="process", stage_name="A2")
    
    B1.set_tree_context(next_stages=[C], stage_mode="process", stage_name="B1")
    B2.set_tree_context(next_stages=[C], stage_mode="process", stage_name="B2")
    B3.set_tree_context(next_stages=[C], stage_mode="process", stage_name="B3")

    C.set_tree_context(stage_mode="process", stage_name="C")

    # 构建任务树
    tree = TaskTree([A1, A2])
    tree.set_reporter(True, host="127.0.0.1", port=5005)

    # 初始任务（输入层）
    init_tasks = {
        A1.get_stage_tag(): range(1, 11),
        A2.get_stage_tag(): range(11, 21),
    }

    tree.start_tree(init_tasks)

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
    A1.set_tree_context(next_stages=[B1], stage_mode="process", stage_name="A1")
    A2.set_tree_context(next_stages=[B2, C1], stage_mode="process", stage_name="A2")

    B1.set_tree_context(next_stages=[C1], stage_mode="process", stage_name="B1")
    B2.set_tree_context(next_stages=[C1], stage_mode="process", stage_name="B2")

    C1.set_tree_context(next_stages=[D1, D2], stage_mode="process", stage_name="C1")

    D1.set_tree_context(stage_mode="process", stage_name="D1")
    D2.set_tree_context(stage_mode="process", stage_name="D2")

    # 构建任务图
    tree = TaskTree([A1, A2])
    tree.set_reporter(True, host="127.0.0.1", port=5005)

    # 初始任务输入
    init_tasks = {
        A1.get_stage_tag(): [0.1, 0.5, 0.9],
        A2.get_stage_tag(): [1.1, 1.5, 2.0],
    }

    tree.start_tree(init_tasks)

def test_star():
    # 定义核心与边节点函数
    core = TaskManager(func=square)
    side1 = TaskManager(func=add_5)
    side2 = TaskManager(func=add_10)
    side3 = TaskManager(func=add_15)

    # 构造 TaskStar
    star = TaskStar(core_stage=core, side_stages=[side1, side2, side3])
    star.set_reporter(True, host="127.0.0.1", port=5005)

    star.start_star({
        core.get_stage_tag(): range(1,11)
    })

def test_fanin():
    # 创建 3 个节点，每个节点有不同偏移
    source1 = TaskManager(func=add_5)
    source2 = TaskManager(func=add_10)
    source3 = TaskManager(func=square)
    merge = TaskManager(func=add_sleep)

    # 构造 TaskFanIn
    fainin = TaskFanIn([source1, source2, source3], merge_stage=merge)
    fainin.set_reporter(True, host="127.0.0.1", port=5005)

    fainin.start_fanin({
        source1.get_stage_tag(): range(1, 11),
        source2.get_stage_tag(): range(11, 21),
        source3.get_stage_tag(): range(21, 31),
    })

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