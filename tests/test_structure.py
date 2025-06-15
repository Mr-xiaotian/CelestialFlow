import pytest, logging
from time import sleep
from celestialflow import TaskManager, TaskTree, TaskLoop


def add_sleep(n):
    sleep(1)
    if n > 30:
        raise ValueError("Test error for greater than 30")
    elif n == 0:
        raise ValueError("Test error for 0")
    elif n == None:
        raise ValueError("Test error for None")
    return n + 1

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

def test_forest_0():
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
    stageD = TaskManager(add_sleep, execution_mode="thread", worker_limit=2)
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
        stageA.get_stage_tag(): range(10),
        stageB.get_stage_tag(): range(11,21)
    }

    tree.start_tree(init_tasks)