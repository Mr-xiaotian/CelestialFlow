import pytest
from celestialflow.graph.util_serialize import build_structure_graph, format_structure_list_from_graph
from celestialflow.stage.core_stage import TaskStage


# 辅助函数
async def async_noop(x):
    """测试用异步空操作函数。"""
    return x


def make_stage(name: str, stage_mode: str, execution_mode: str) -> TaskStage:
    """根据模式组合构造测试节点。"""
    func = async_noop if execution_mode == "async" else (lambda x: x)
    return TaskStage(name, func, stage_mode=stage_mode, execution_mode=execution_mode, max_workers=2)


class TestUtilSerialize:
    @pytest.fixture
    def mock_graph_data(self):
        """构造一组 DAG 与环图序列化测试样本。"""
        s1 = make_stage("s1", "serial", "serial")
        s2 = make_stage("s2", "thread", "async")
        s3 = make_stage("s3", "serial", "serial")
        s4 = make_stage("s4", "thread", "thread")

        stage_dict = {s.get_name(): s for s in [s1, s2, s3, s4]}

        out_edges = {
            s1.get_name(): [s2.get_name(), s3.get_name()],
            s2.get_name(): [s4.get_name()],
            s3.get_name(): [s4.get_name()],
            s4.get_name(): [],
        }

        cs1 = make_stage("cs1", "serial", "serial")
        cs2 = make_stage("cs2", "serial", "serial")
        cs3 = make_stage("cs3", "serial", "serial")

        cyclic_stage_dict = {s.get_name(): s for s in [cs1, cs2, cs3]}

        cyclic_out_edges = {
            cs1.get_name(): [cs2.get_name()],
            cs2.get_name(): [cs3.get_name()],
            cs3.get_name(): [cs1.get_name()],
        }

        return {
            "s1": s1,
            "stage_dict": stage_dict,
            "out_edges": out_edges,
            "cs1": cs1,
            "cyclic_stage_dict": cyclic_stage_dict,
            "cyclic_out_edges": cyclic_out_edges,
        }

    def test_build_structure_graph_dag(self, mock_graph_data):
        """验证 DAG 结构会被递归展开并复用引用节点。"""
        s1 = mock_graph_data["s1"]
        stage_dict = mock_graph_data["stage_dict"]
        out_edges = mock_graph_data["out_edges"]

        graphs = build_structure_graph([s1], out_edges, stage_dict)
        assert len(graphs) == 1
        graph = graphs[0]

        assert graph["name"] == "s1"
        assert len(graph["next_stages"]) == 2
        assert graph["next_stages"][0]["name"] == "s2"
        assert graph["next_stages"][1]["name"] == "s3"
        assert graph["next_stages"][0]["next_stages"][0]["name"] == "s4"
        assert graph["next_stages"][1]["next_stages"][0]["name"] == "s4"
        assert graph["next_stages"][1]["next_stages"][0]["is_ref"] is True

    def test_build_structure_graph_cyclic(self, mock_graph_data):
        """验证环图结构会在回边处标记引用节点。"""
        cs1 = mock_graph_data["cs1"]
        cyclic_stage_dict = mock_graph_data["cyclic_stage_dict"]
        cyclic_out_edges = mock_graph_data["cyclic_out_edges"]

        graphs = build_structure_graph([cs1], cyclic_out_edges, cyclic_stage_dict)
        assert len(graphs) == 1
        graph = graphs[0]

        assert graph["name"] == "cs1"
        assert graph["next_stages"][0]["name"] == "cs2"
        assert graph["next_stages"][0]["next_stages"][0]["name"] == "cs3"
        assert graph["next_stages"][0]["next_stages"][0]["next_stages"][0]["name"] == "cs1"
        assert graph["next_stages"][0]["next_stages"][0]["next_stages"][0]["is_ref"] is True

    def test_format_structure_list_from_graph(self, mock_graph_data):
        """验证结构图能够格式化为可读的结构列表。"""
        s1 = mock_graph_data["s1"]
        stage_dict = mock_graph_data["stage_dict"]
        out_edges = mock_graph_data["out_edges"]

        graphs = build_structure_graph([s1], out_edges, stage_dict)
        formatted_list = format_structure_list_from_graph(graphs)

        assert len(formatted_list) > 0
        assert "s1::<lambda> (S:serial, E:serial, W:2)" in formatted_list[1]
        assert any("[Ref]" in line for line in formatted_list)
