from typing import List

from .task_manage import TaskManager
from .task_graph import TaskGraph
from .task_support import StageStatus

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


class TaskCross(TaskGraph):
    def __init__(self, layers: List[List[TaskManager]], layout_mode: str = "serial"):
        """
        TaskCross: 多层任务交叉结构

        该结构将任务按“层”组织，每层可以包含多个并行执行的 TaskManager 节点，
        不同层之间通过依赖关系连接，形成跨层的数据流图。

        :param layers: List[List[TaskManager]]
            按层划分的任务节点列表。每个子列表代表一层，列表中的 TaskManager 将并行执行。
            相邻层之间的所有节点将建立全连接依赖（即每个上一层节点都连接到下一层所有节点）。

        :param layout_mode: str, default = 'serial'
            控制任务图的调度布局模式：
            - 'serial'：逐层顺序执行，上一层全部完成后才启动下一层；
            - 'process'：所有层并行启动，执行顺序由依赖关系自动调度。
        """
        for i in range(len(layers)):
            curr_layer = layers[i]
            next_layer = layers[i + 1] if i < len(layers) - 1 else []
            for index, stage in enumerate(curr_layer[:]):
                # 非最后一层连接为并行
                stage.set_graph_context(
                    next_stages=next_layer,
                    stage_mode="process",
                    stage_name=f"Layer{i+1}-{index+1}"
                )
        super().__init__(layers[0])

        self.layers = layers
        self.layout_mode = layout_mode

    def start_cross(self, init_tasks_dict: dict, put_termination_signal: bool = True):
        """
        启动多层交叉结构任务图
        """
        self.start_graph(init_tasks_dict, put_termination_signal)

    def _excute_stages(self):
        if self.layout_mode == "process":
            # 默认逻辑：一次性执行所有节点
            for tag in self.stages_status_dict:
                self._execute_stage(self.stages_status_dict[tag]["stage"])

            for p in self.processes:
                p.join()
                self.stages_status_dict[p.name]["status"] = StageStatus.STOPPED
                self.task_logger._log("DEBUG", f"{p.name} exitcode: {p.exitcode}")
        else:
            # serial layout_mode：一层层地顺序执行
            for layer in self.layers:
                processes = []
                for stage in layer:
                    self._execute_stage(stage)
                    if stage.stage_mode == "process":
                        processes.append(self.processes[-1])  # 最新的进程

                # join 当前层的所有进程（如果有）
                for p in processes:
                    p.join()
                    self.stages_status_dict[p.name]["status"] = StageStatus.STOPPED
                    self.task_logger._log("DEBUG", f"{p.name} exitcode: {p.exitcode}")


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
