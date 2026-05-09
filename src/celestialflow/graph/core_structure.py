# graph/core_structure.py
from ..stage import TaskStage
from .core_graph import TaskGraph


# ========有向无环图(DAG)========
class TaskChain(TaskGraph):
    """线性任务链，将多个 Stage 按顺序串行或并行连接。"""

    def __init__(
        self,
        stages: list[TaskStage],
        chain_mode: str = "serial",
        log_level: str = "SUCCESS",
    ) -> None:
        """
        TaskChain: 线性任务链结构
        该结构将多个 TaskStage 节点按顺序连接，形成一个线性的数据流图。

        :param stages: TaskStage 列表, 每个 TaskStage 节点将连接到下一个节点
        :param chain_mode: 控制任务链中各节点的运行模式, 可选 'serial' 或 'thread'
        :param log_level: 日志级别
        """
        super().__init__(schedule_mode="eager", log_level=log_level)

        for num, stage in enumerate(stages):
            stage.set_stage_mode(chain_mode)
            stage.set_name(f"Stage {num + 1}")

        self.set_stages(root_stages=[stages[0]], stages=stages)
        for num in range(len(stages) - 1):
            self.connect([stages[num]], [stages[num + 1]])

    def start_chain(
        self, init_tasks_dict: dict, put_termination_signal: bool = True
    ) -> None:
        """
        启动任务链

        :param init_tasks_dict: 初始化任务字典
        :param put_termination_signal: 是否在任务完成后发送终止信号
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


class TaskCross(TaskGraph):
    """多层交叉结构，每层内部并行，层之间全连接。"""

    def __init__(
        self,
        layers: list[list[TaskStage]],
        schedule_mode: str = "eager",
        log_level: str = "SUCCESS",
    ) -> None:
        """
        TaskCross: 多层任务交叉结构
        该结构将任务按"层"组织，每层可以包含多个并行执行的 TaskStage 节点，
        不同层之间通过依赖关系连接，形成跨层的数据流图。

        :param layers:
            按层划分的任务节点列表。每个子列表代表一层，列表中的 TaskStage 将并行执行。
            相邻层之间的所有节点将建立全连接依赖（即每个上一层节点都连接到下一层所有节点）。
        :param schedule_mode: 控制任务图的调度布局模式
        :param log_level: 日志级别
        """
        super().__init__(schedule_mode=schedule_mode, log_level=log_level)

        all_stages = []
        for i, curr_layer in enumerate(layers):
            for index, stage in enumerate(curr_layer):
                stage.set_stage_mode("thread")
                stage.set_name(f"Layer{i + 1}-{index + 1}")
            all_stages.extend(curr_layer)

        self.set_stages(root_stages=layers[0], stages=all_stages)
        for i in range(len(layers) - 1):
            self.connect(layers[i], layers[i + 1])

    def start_cross(
        self, init_tasks_dict: dict, put_termination_signal: bool = True
    ) -> None:
        """
        启动多层交叉结构任务图

        :param init_tasks_dict: 初始化任务字典
        :param put_termination_signal: 是否在任务完成后发送终止信号
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


class TaskGrid(TaskGraph):
    """二维网格结构，每个节点连接右侧和下方的邻居。"""

    def __init__(
        self,
        grid: list[list[TaskStage]],
        schedule_mode: str = "eager",
        log_level: str = "SUCCESS",
    ) -> None:
        """
        TaskGrid: 任务网格结构
        该结构将任务节点组织成二维网格形式，每个节点连接其右侧和下方的节点，
        形成一个网格状的数据流图。

        :param grid:
            任务网格，每个子列表代表一行，列表中的 TaskStage 将按行并行执行。
            每个节点将连接到其右侧和下方的节点。
        :param schedule_mode: 控制任务图的调度布局模式
        :param log_level: 日志级别
        """
        super().__init__(schedule_mode=schedule_mode, log_level=log_level)

        rows, cols = len(grid), len(grid[0])
        all_stages = []
        for i in range(rows):
            for j in range(cols):
                curr = grid[i][j]
                curr.set_stage_mode("thread")
                curr.set_name(f"Grid-{i + 1}-{j + 1}")
                all_stages.append(curr)

        self.set_stages(root_stages=[grid[0][0]], stages=all_stages)
        for i in range(rows):
            for j in range(cols):
                curr = grid[i][j]
                if i + 1 < rows:
                    self.connect([curr], [grid[i + 1][j]])
                if j + 1 < cols:
                    self.connect([curr], [grid[i][j + 1]])

    def start_grid(
        self, init_tasks_dict: dict, put_termination_signal: bool = True
    ) -> None:
        """
        启动任务网格结构

        :param init_tasks_dict: 初始化任务字典
        :param put_termination_signal: 是否在任务完成后发送终止信号
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


# ========有环图========
class TaskLoop(TaskGraph):
    """有环图结构，节点首尾相连形成闭环。"""

    def __init__(self, stages: list[TaskStage], log_level: str = "SUCCESS") -> None:
        """
        TaskLoop:  任务环结构
        由于环的结构特性, 强制使用 'eager' 节点模式

        :param stages: TaskStage 列表, 每个 TaskStage 节点将连接到下一个节点, 形成一个闭环
        :param log_level: 日志级别
        """
        super().__init__(log_level=log_level)

        for num, stage in enumerate(stages):
            stage.set_stage_mode("thread")
            stage.set_name(f"Stage {num + 1}")

        self.set_stages(root_stages=[stages[0]], stages=stages)
        for num in range(len(stages)):
            next_stage = stages[num + 1] if num < len(stages) - 1 else stages[0]
            self.connect([stages[num]], [next_stage])

    def start_loop(
        self, init_tasks_dict: dict, put_termination_signal: bool = False
    ) -> None:
        """
        启动任务环, 环是自锁结构, 建议外部注入式停止

        :param init_tasks_dict: 任务列表
        :param put_termination_signal: 是否在任务完成后发送终止信号
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


class TaskWheel(TaskGraph):
    """轮状结构，中心节点连接到一个环上。"""

    def __init__(
        self, center: TaskStage, ring: list[TaskStage], log_level: str = "SUCCESS"
    ) -> None:
        """
        wheel: 特殊的有环图, 他有结构意义上的起点, 中心节点连向环, 环相连成闭环
        由于环的结构特性, 强制使用 'eager' 节点模式

        :param center: 中心节点
        :param ring: 环节点
        :param log_level: 日志级别
        """
        super().__init__(log_level=log_level)

        center.set_stage_mode("thread")
        center.set_name("Center")

        for i, node in enumerate(ring):
            node.set_stage_mode("thread")
            node.set_name(f"Ring-{i + 1}")

        self.set_stages(root_stages=[center], stages=[center] + ring)
        self.connect([center], ring)
        for i, node in enumerate(ring):
            next_stage = ring[(i + 1) % len(ring)]
            self.connect([node], [next_stage])

    def start_wheel(
        self, init_tasks_dict: dict, put_termination_signal: bool = True
    ) -> None:
        """
        启动任务轮结构

        :param init_tasks_dict: 任务列表
        :param put_termination_signal: 是否注入终止信号
        """
        self.start_graph(init_tasks_dict, put_termination_signal)


class TaskComplete(TaskGraph):
    """完全图结构，每个节点都连接到除自己以外的所有其他节点。"""

    def __init__(self, stages: list[TaskStage], log_level: str = "SUCCESS") -> None:
        """
        TaskComplete: 完全图结构，每个节点都连向除自己以外的所有其他节点

        :param stages: 所有 TaskStage 节点
        :param log_level: 日志级别
        """
        super().__init__(log_level=log_level)

        for i, stage in enumerate(stages):
            stage.set_stage_mode("thread")
            stage.set_name(f"Node {i + 1}")

        self.set_stages(root_stages=stages, stages=stages)
        for i, stage in enumerate(stages):
            others = [s for j, s in enumerate(stages) if i != j]
            self.connect([stage], others)

    def start_complete(
        self, init_tasks_dict: dict, put_termination_signal: bool = False
    ) -> None:
        """
        启动任务完全图, 建议外部注入式停止

        :param init_tasks_dict: 任务列表
        :param put_termination_signal: 是否在任务完成后发送终止信号
        """
        self.start_graph(init_tasks_dict, put_termination_signal)
