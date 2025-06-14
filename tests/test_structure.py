import pytest, logging
from time import sleep
from celestialflow import TaskManager, TaskLoop


def add_sleep(n):
    sleep(1)
    if n > 30:
        raise ValueError("Test error for greater than 30")
    elif n == 0:
        raise ValueError("Test error for 0")
    return n + 1

def test_loop():
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