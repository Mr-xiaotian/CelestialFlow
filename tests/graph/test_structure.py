import pytest

from celestialflow import (
    TaskChain,
    TaskComplete,
    TaskCross,
    TaskGrid,
    TaskLoop,
    TaskStage,
    TaskWheel,
)
from celestialflow.runtime.util_errors import InvalidStructureError


def add_one(x: int) -> int:
    """测试用同步加一函数。"""
    return x + 1


def double(x: int) -> int:
    """测试用同步乘二函数。"""
    return x * 2


def to_str(x: int) -> str:
    """测试用同步转字符串函数。"""
    return str(x)


# =========================
# TaskLoop 测试
# =========================
class TestTaskLoop:
    def test_loop_analysis(self):
        """测试 TaskLoop 的结构分析：应识别为非 DAG，且所有环内节点处于同一逻辑层级"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)
        s3 = TaskStage("s3", to_str)

        loop = TaskLoop("test_loop_analysis", [s1, s2, s3])
        s1.put_tasks([1], put_termination_signal=True)
        loop.start_graph()

        analysis = loop.get_graph_analysis()
        assert analysis["isDAG"] is False

        layers = analysis["layersDict"]
        stage_names = {s1.get_name(), s2.get_name(), s3.get_name()}
        for layer_names in layers.values():
            if s1.get_name() in layer_names:
                assert stage_names.issubset(set(layer_names))
                break

    def test_loop_source_stages(self):
        """测试 TaskLoop 的源节点推导：对于纯环结构，应返回环内的一个代表节点作为注入点"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)

        loop = TaskLoop("test_loop_source_stages", [s1, s2])
        s1.put_tasks([1], put_termination_signal=True)
        loop.start_graph()

        sources = loop.get_source_stages()
        assert len(sources) == 1
        assert sources[0].get_name() in {s1.get_name(), s2.get_name()}


# =========================
# TaskWheel 测试
# =========================
class TestTaskWheel:
    def test_wheel_analysis(self):
        """测试 TaskWheel 的结构分析：Center 应在第 0 层，Ring 节点应在第 1 层"""
        center = TaskStage("center", add_one)
        r1 = TaskStage("r1", double)
        r2 = TaskStage("r2", to_str)
        r3 = TaskStage("r3", add_one)

        wheel = TaskWheel("test_wheel_analysis", center, [r1, r2, r3])
        wheel.set_graph_mode("thread", "serial")

        analysis = wheel.get_graph_analysis()
        assert analysis["isDAG"] is False

        layers = analysis["layersDict"]
        assert center.get_name() in layers[0]
        ring_names = {r1.get_name(), r2.get_name(), r3.get_name()}
        assert ring_names.issubset(set(layers[1]))

    def test_wheel_source_stages(self):
        """测试 TaskWheel 的源节点推导：应仅返回 Center 节点作为唯一入口"""
        center = TaskStage("center", add_one)
        r1 = TaskStage("r1", double)
        r2 = TaskStage("r2", to_str)

        wheel = TaskWheel("test_wheel_source_stages", center, [r1, r2])
        wheel.set_graph_mode("thread", "serial")

        sources = wheel.get_source_stages()
        assert len(sources) == 1
        assert sources[0].get_name() == center.get_name()


# =========================
# 结构输入校验测试
# =========================
class TestStructureValidation:
    """空输入/非法输入校验：应抛出 ValueError 而非崩溃或静默构造空图。"""

    def test_chain_empty_stages_raises(self):
        """TaskChain 空 stages 应抛出 InvalidStructureError。"""
        with pytest.raises(InvalidStructureError):
            TaskChain("c", [])

    def test_cross_empty_layers_raises(self):
        """TaskCross 空 layers 应抛出 InvalidStructureError。"""
        with pytest.raises(InvalidStructureError):
            TaskCross("x", [])

    def test_cross_empty_layer_raises(self):
        """TaskCross 包含空层应抛出 InvalidStructureError。"""
        s1 = TaskStage("s1", add_one)
        with pytest.raises(InvalidStructureError):
            TaskCross("x", [[], [s1]])

    def test_grid_empty_raises(self):
        """TaskGrid 空网格应抛出 InvalidStructureError 而非 IndexError。"""
        with pytest.raises(InvalidStructureError):
            TaskGrid("g", [])

    def test_grid_empty_row_raises(self):
        """TaskGrid 首行为空应抛出 InvalidStructureError。"""
        with pytest.raises(InvalidStructureError):
            TaskGrid("g", [[]])

    def test_grid_ragged_rows_raises(self):
        """TaskGrid 行长度不一致应抛出 InvalidStructureError。"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)
        with pytest.raises(InvalidStructureError):
            TaskGrid("g", [[s1, s2], [s2]])

    def test_loop_empty_stages_raises(self):
        """TaskLoop 空 stages 应抛出 InvalidStructureError。"""
        with pytest.raises(InvalidStructureError):
            TaskLoop("l", [])

    def test_wheel_empty_ring_raises(self):
        """TaskWheel 空 ring 应抛出 InvalidStructureError。"""
        center = TaskStage("center", add_one)
        with pytest.raises(InvalidStructureError):
            TaskWheel("w", center, [])

    def test_complete_single_node_raises(self):
        """TaskComplete 单节点（无法构成边）应抛出 InvalidStructureError。"""
        s1 = TaskStage("s1", add_one)
        with pytest.raises(InvalidStructureError):
            TaskComplete("c", [s1])

    def test_complete_empty_stages_raises(self):
        """TaskComplete 空 stages 应抛出 InvalidStructureError。"""
        with pytest.raises(InvalidStructureError):
            TaskComplete("c", [])
