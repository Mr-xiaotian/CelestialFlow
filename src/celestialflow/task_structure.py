from typing import List

from .task_manage import TaskManager
from .task_graph import TaskGraph


class TaskChain(TaskGraph):
    def __init__(self, stages: List[TaskManager], chain_mode: str = "serial"):
        """
        初始化 TaskChain
        :param stages: TaskManager 列表
        :param chain_mode: 链式模式，默认为 'serial'
        """
        for num, stage in enumerate(stages):
            stage_name = f"Stage {num + 1}"
            next_stages = [stages[num + 1]] if num < len(stages) - 1 else []
            stage.set_graph_context(next_stages, chain_mode, stage_name)

        root_stage = stages[0]
        super().__init__([root_stage])

    def start_chain(self, init_tasks_dict: dict, put_termination_signal: bool=True):
        """
        启动任务链
        :param init_tasks_dict: 任务列表
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


class TaskLoop(TaskGraph):
    def __init__(self, stages: List[TaskManager]):
        """
        初始化 TaskLoop, 由于环的结构特性, 强制使用 'process' 节点模式
        :param stages: TaskManager 列表
        """
        for num, stage in enumerate(stages):
            stage_name = f"Stage {num + 1}"
            next_stages = [stages[num + 1]] if num < len(stages) - 1 else [stages[0]]
            stage.set_graph_context(next_stages, "process", stage_name)

        root_stage = stages[0]
        super().__init__([root_stage])

    def start_loop(self, init_tasks_dict: dict):
        """
        启动任务环, 环是自锁结构, 能且仅能外部注入式停止
        :param init_tasks_dict: 任务列表
        """
        self.start_graph(init_tasks_dict, False)


class TaskStar(TaskGraph):
    def __init__(self, core_stage: TaskManager, side_stages: List[TaskManager], star_mode: str = "serial"):
        """
        TaskStar: 一个中心节点连接多个子节点（旁点）
        :param core_stage: 核心 TaskManager 节点
        :param side_stages: 所有旁支节点列表
        """
        # 设置核心节点指向所有旁支
        core_stage.set_graph_context(side_stages, star_mode, "Core Stage")

        for idx, side in enumerate(side_stages):
            side.set_graph_context(stage_mode="process", stage_name=f"Side Stage {idx + 1}")

        super().__init__([core_stage])

    def start_star(self, init_tasks_dict: dict, put_termination_signal: bool=True):
        """
        启动任务星
        :param init_tasks_dict: 任务列表
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


class TaskFanIn(TaskGraph):
    def __init__(self, source_stages: List[TaskManager], merge_stage: TaskManager):
        """
        TaskFanIn: 多源输入 → 单节点聚合
        :param source_stages: 输入 TaskManager 节点列表
        :param sink_stage: 聚合节点
        :param sink_mode: 聚合节点执行模式（默认为 serial）
        """
        for idx, source in enumerate(source_stages):
            source.set_graph_context(next_stages=[merge_stage], stage_mode="process", stage_name=f"Source {idx+1}")
        merge_stage.set_graph_context(stage_mode="serial", stage_name="Merge Stage")

        super().__init__(source_stages)

    def start_fanin(self, init_tasks_dict: dict, put_termination_signal: bool=True):
        """
        启动 Fan-In 结构任务图
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


class TaskCross(TaskGraph):
    def __init__(self, layers: List[List[TaskManager]]):
        """
        TaskCross: 多层交叉结构
        :param layers: 每层 TaskManager 节点列表
        """
        for i in range(len(layers) - 1):
            for stage in layers[i]:
                stage.set_graph_context(layers[i+1], "process", f"Layer{i+1}-{stage.func.__name__}")

        super().__init__(layers[0])

    def start_cross(self, init_tasks_dict: dict, put_termination_signal: bool=True):
        """
        启动多层交叉结构任务图
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


class TaskComplete(TaskGraph):
    def __init__(self, stages: List[TaskManager]):
        """
        TaskComplete: 完全图结构，每个节点都连向除自己以外的所有其他节点
        :param stages: 所有 TaskManager 节点
        """
        for i, stage in enumerate(stages):
            next_stages = [s for j, s in enumerate(stages) if i != j]
            stage.set_graph_context(next_stages=next_stages, stage_mode="process", stage_name=f"Node {i + 1}")

        super().__init__(stages)

    def start_complete(self, init_tasks_dict: dict):
        """
        启动任务完全图
        :param init_tasks_dict: 任务列表
        """
        self.start_graph(init_tasks_dict, False)
