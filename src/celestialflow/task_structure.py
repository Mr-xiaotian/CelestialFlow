from typing import List

from .task_stage import TaskStage
from .task_graph import TaskGraph


# ========有向无环图(DAG)========
class TaskChain(TaskGraph):
    def __init__(self, stages: List[TaskStage], chain_mode: str = "serial"):
        """
        TaskChain: 线性任务链结构
        该结构将多个 TaskStage 节点按顺序连接，形成一个线性的数据流图。

        :param stages: TaskStage 列表, 每个 TaskStage 节点将连接到下一个节点
        :param chain_mode: 控制任务链中各节点同时运行(process), 亦或者依次运行(serial)
        """
        for num, stage in enumerate(stages):
            stage_name = f"Stage {num + 1}"
            next_stages = [stages[num + 1]] if num < len(stages) - 1 else []
            stage.set_graph_context(next_stages, chain_mode, stage_name)

        root_stage = stages[0]
        super().__init__([root_stage])

    def start_chain(self, init_tasks_dict: dict, put_termination_signal: bool = True):
        """
        启动任务链

        :param init_tasks_dict: 初始化任务字典
        :param put_termination_signal: 是否在任务完成后发送终止信号
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


class TaskCross(TaskGraph):
    def __init__(self, layers: List[List[TaskStage]], schedule_mode: str = "eager"):
        """
        TaskCross: 多层任务交叉结构
        该结构将任务按“层”组织，每层可以包含多个并行执行的 TaskStage 节点，
        不同层之间通过依赖关系连接，形成跨层的数据流图。

        :param layers: 
            按层划分的任务节点列表。每个子列表代表一层，列表中的 TaskStage 将并行执行。
            相邻层之间的所有节点将建立全连接依赖（即每个上一层节点都连接到下一层所有节点）。
        :param schedule_mode: 
            控制任务图的调度布局模式
        """
        for i in range(len(layers)):
            curr_layer = layers[i]
            next_layer = layers[i + 1] if i < len(layers) - 1 else []
            for index, stage in enumerate(curr_layer[:]):
                # 非最后一层连接为并行
                stage.set_graph_context(
                    next_stages=next_layer,
                    stage_mode="process",
                    stage_name=f"Layer{i+1}-{index+1}",
                )
        super().__init__(layers[0], schedule_mode)

    def start_cross(self, init_tasks_dict: dict, put_termination_signal: bool = True):
        """
        启动多层交叉结构任务图

        :param init_tasks_dict: 初始化任务字典
        :param put_termination_signal: 是否在任务完成后发送终止信号
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


class TaskGrid(TaskGraph):
    def __init__(self, grid: List[List[TaskStage]], schedule_mode: str = "eager"):
        """
        TaskGrid: 任务网格结构
        该结构将任务节点组织成二维网格形式，每个节点连接其右侧和下方的节点，
        形成一个网格状的数据流图。

        :param grid: 
            任务网格，每个子列表代表一行，列表中的 TaskStage 将按行并行执行。
            每个节点将连接到其右侧和下方的节点。
        :param schedule_mode: 控制任务图的调度布局模式
        """
        rows, cols = len(grid), len(grid[0])
        for i in range(rows):
            for j in range(cols):
                curr = grid[i][j]
                nexts = []
                if i + 1 < rows:
                    nexts.append(grid[i + 1][j])  # down
                if j + 1 < cols:
                    nexts.append(grid[i][j + 1])  # right
                curr.set_graph_context(nexts, "process", f"Grid-{i+1}-{j+1}")
        super().__init__([grid[0][0]], schedule_mode)  # 起点为左上角

    def start_grid(self, init_tasks_dict: dict, put_termination_signal: bool = True):
        """
        启动任务网格结构

        :param init_tasks_dict: 初始化任务字典
        :param put_termination_signal: 是否在任务完成后发送终止信号
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


# ========有环图========
class TaskLoop(TaskGraph):
    def __init__(self, stages: List[TaskStage]):
        """
        TaskLoop:  任务环结构
        由于环的结构特性, 强制使用 'eager' 节点模式

        :param stages: TaskStage 列表, 每个 TaskStage 节点将连接到下一个节点, 形成一个闭环
        """
        for num, stage in enumerate(stages):
            stage_name = f"Stage {num + 1}"
            next_stages = [stages[num + 1]] if num < len(stages) - 1 else [stages[0]]
            stage.set_graph_context(next_stages, "process", stage_name)

        super().__init__([stages[0]])

    def start_loop(self, init_tasks_dict: dict, put_termination_signal: bool = False):
        """
        启动任务环, 环是自锁结构, 建议外部注入式停止

        :param init_tasks_dict: 任务列表
        :param put_termination_signal: 是否在任务完成后发送终止信号
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


class TaskWheel(TaskGraph):
    def __init__(self, center: TaskStage, ring: List[TaskStage]):
        """
        wheel: 特殊的有环图, 他有结构意义上的起点, 中心节点连向环, 环相连成闭环
        由于环的结构特性, 强制使用 'eager' 节点模式

        :param center: 中心节点
        :param ring: 环节点
        """
        # 中心连向环
        center.set_graph_context(ring, "process", "Center")
        # 环相连（成闭环）
        for i, node in enumerate(ring):
            next_stage = ring[(i + 1) % len(ring)]
            node.set_graph_context([next_stage], "process", f"Ring-{i+1}")
        super().__init__([center])

    def start_wheel(self, init_tasks_dict: dict, put_termination_signal: bool = True):
        """
        启动任务轮结构

        :param init_tasks_dict: 任务列表
        :param put_termination_signal: 是否注入终止信号
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


class TaskComplete(TaskGraph):
    def __init__(self, stages: List[TaskStage]):
        """
        TaskComplete: 完全图结构，每个节点都连向除自己以外的所有其他节点

        :param stages: 所有 TaskStage 节点
        """
        for i, stage in enumerate(stages):
            next_stages = [s for j, s in enumerate(stages) if i != j]
            stage.set_graph_context(
                next_stages=next_stages,
                stage_mode="process",
                stage_name=f"Node {i + 1}",
            )

        super().__init__(stages)

    def start_complete(self, init_tasks_dict: dict, put_termination_signal: bool = False):
        """
        启动任务完全图, 建议外部注入式停止

        :param init_tasks_dict: 任务列表
        :param put_termination_signal: 是否在任务完成后发送终止信号
        """
        self.start_graph(init_tasks_dict, put_termination_signal)
