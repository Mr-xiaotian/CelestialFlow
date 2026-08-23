# graph/core_structure.py
from ..runtime.util_errors import InvalidStructureError
from ..stage.util_types import AnyTaskStage
from .core_graph import TaskGraph


# ==== 有向无环图（DAG） ====
class TaskChain(TaskGraph):
    """线性任务链，将多个 Stage 按顺序串行或并行连接。"""

    def __init__(
        self,
        name: str,
        stages: list[AnyTaskStage],
        graph_mode: str = "thread",
    ) -> None:
        """
        TaskChain: 线性任务链结构
        该结构将多个 TaskStage 节点按顺序连接，形成一个线性的数据流图。

        :param stages: TaskStage 列表, 每个 TaskStage 节点将连接到下一个节点
        :param graph_mode: 图执行模式, 可选值为 'serial'、'thread' 或 'async'，
            默认 'thread'
        :raises InvalidStructureError: stages 为空时抛出
        """
        if not stages:
            raise InvalidStructureError("stages must not be empty")

        super().__init__(name=name, graph_mode=graph_mode)

        self.set_stages(stages)
        for num in range(len(stages) - 1):
            self.connect([stages[num]], [stages[num + 1]])


class TaskCross(TaskGraph):
    """多层交叉结构，每层内部并行，层之间全连接。"""

    def __init__(
        self,
        name: str,
        layers: list[list[AnyTaskStage]],
        graph_mode: str = "thread",
    ) -> None:
        """
        TaskCross: 多层任务交叉结构
        该结构将任务按"层"组织，每层可以包含多个并行执行的 TaskStage 节点，
        不同层之间通过依赖关系连接，形成跨层的数据流图。

        :param layers:
            按层划分的任务节点列表。每个子列表代表一层，列表中的 TaskStage 将并行执行。
            相邻层之间的所有节点将建立全连接依赖（即每个上一层节点都连接到下一层所有节点）。
        :param graph_mode: 图执行模式, 可选值为 'serial'、'thread' 或 'async'，
            默认 'thread'
        :raises InvalidStructureError: layers 为空或包含空层时抛出
        """
        if not layers or any(not layer for layer in layers):
            raise InvalidStructureError(
                "layers must not be empty and must not contain empty layers"
            )

        super().__init__(name=name, graph_mode=graph_mode)

        all_stages: list[AnyTaskStage] = []
        for curr_layer in layers:
            all_stages.extend(curr_layer)

        self.set_stages(all_stages)
        for i in range(len(layers) - 1):
            self.connect(layers[i], layers[i + 1])


class TaskGrid(TaskGraph):
    """二维网格结构，每个节点连接右侧和下方的邻居。"""

    def __init__(
        self,
        name: str,
        grid: list[list[AnyTaskStage]],
        graph_mode: str = "thread",
    ) -> None:
        """
        TaskGrid: 任务网格结构
        该结构将任务节点组织成二维网格形式，每个节点连接其右侧和下方的节点，
        形成一个网格状的数据流图。

        :param grid:
            任务网格，每个子列表代表一行，列表中的 TaskStage 将按行并行执行。
            每个节点将连接到其右侧和下方的节点。
        :param graph_mode: 图执行模式, 可选值为 'serial'、'thread' 或 'async'，
            默认 'thread'
        :raises InvalidStructureError: grid 为空、首行为空或各行长度不一致时抛出
        """
        if not grid or not grid[0]:
            raise InvalidStructureError("grid must not be empty")
        if any(len(row) != len(grid[0]) for row in grid):
            raise InvalidStructureError("all grid rows must have the same length")

        super().__init__(name=name, graph_mode=graph_mode)

        rows, cols = len(grid), len(grid[0])
        all_stages: list[AnyTaskStage] = []
        for i in range(rows):
            for j in range(cols):
                curr = grid[i][j]
                all_stages.append(curr)

        self.set_stages(all_stages)
        for i in range(rows):
            for j in range(cols):
                curr = grid[i][j]
                if i + 1 < rows:
                    self.connect([curr], [grid[i + 1][j]])
                if j + 1 < cols:
                    self.connect([curr], [grid[i][j + 1]])


# ==== 有环图 ====
class TaskLoop(TaskGraph):
    """有环图结构，节点首尾相连形成闭环。"""

    def __init__(
        self,
        name: str,
        stages: list[AnyTaskStage],
        graph_mode: str = "thread",
    ) -> None:
        """
        TaskLoop:  任务环结构

        :param stages: TaskStage 列表, 每个 TaskStage 节点将连接到下一个节点, 形成一个闭环
        :param graph_mode: 图执行模式, 可选值为 'serial'、'thread' 或 'async'，
            默认 'thread'
        :raises InvalidStructureError: stages 为空时抛出
        """
        if not stages:
            raise InvalidStructureError("stages must not be empty")

        super().__init__(name=name, graph_mode=graph_mode)

        self.set_stages(stages)
        for num in range(len(stages)):
            next_stage = stages[num + 1] if num < len(stages) - 1 else stages[0]
            self.connect([stages[num]], [next_stage])


class TaskWheel(TaskGraph):
    """轮状结构，中心节点连接到一个环上。"""

    def __init__(
        self,
        name: str,
        center: AnyTaskStage,
        ring: list[AnyTaskStage],
        graph_mode: str = "thread",
    ) -> None:
        """
        wheel: 特殊的有环图, 他有结构意义上的起点, 中心节点连向环, 环相连成闭环

        :param center: 中心节点
        :param ring: 环节点
        :param graph_mode: 图执行模式, 可选值为 'serial'、'thread' 或 'async'，
            默认 'thread'
        :raises InvalidStructureError: ring 为空时抛出
        """
        if not ring:
            raise InvalidStructureError("ring must not be empty")

        super().__init__(name=name, graph_mode=graph_mode)

        self.set_stages([center, *ring])
        self.connect([center], ring)
        for i, node in enumerate(ring):
            next_stage = ring[(i + 1) % len(ring)]
            self.connect([node], [next_stage])


class TaskComplete(TaskGraph):
    """完全图结构，每个节点都连接到除自己以外的所有其他节点。"""

    def __init__(
        self,
        name: str,
        stages: list[AnyTaskStage],
        graph_mode: str = "thread",
    ) -> None:
        """
        TaskComplete: 完全图结构，每个节点都连向除自己以外的所有其他节点

        :param stages: 所有 TaskStage 节点
        :param graph_mode: 图执行模式, 可选值为 'serial'、'thread' 或 'async'，
            默认 'thread'
        :raises InvalidStructureError: stages 少于 2 个节点时抛出（完全图至少需要 2 个节点才能构成边）
        """
        if len(stages) < 2:
            raise InvalidStructureError(
                "stages must contain at least 2 nodes to form a complete graph"
            )

        super().__init__(name=name, graph_mode=graph_mode)

        self.set_stages(stages)
        for i, stage in enumerate(stages):
            others = [s for j, s in enumerate(stages) if i != j]
            self.connect([stage], others)
