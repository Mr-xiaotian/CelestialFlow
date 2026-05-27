import pytest
from celestialflow.graph.util_serialize import build_structure_graph, format_structure_list_from_graph
from celestialflow.stage.core_stage import TaskStage
from celestialflow.graph.core_graph import StageRuntime
from celestialflow.runtime.core_queue import TaskInQueue, TaskOutQueue
from celestialflow.persistence.core_log import LogInlet, LogSpout
from queue import Queue

# 辅助函数：创建 mock StageRuntime
async def async_noop(x):
    return x

def create_mock_stage_runtime(name: str, func_name: str, stage_mode: str, execution_mode: str) -> StageRuntime:
    func = async_noop if execution_mode == "async" else (lambda x: x)
    stage = TaskStage(name, func, stage_mode=stage_mode, execution_mode=execution_mode)
    # 模拟队列，虽然这里不实际使用，但 StageRuntime 需要
    log_spout = LogSpout()
    log_spout.start()
    log_inlet = LogInlet(log_spout.get_queue())
    in_queue = TaskInQueue(Queue(), [], stage.get_name(), log_inlet)
    out_queue = TaskOutQueue([], [], stage.get_name(), log_inlet)
    return StageRuntime(stage, in_queue, out_queue)

class TestUtilSerialize:
    @pytest.fixture
    def mock_graph_data(self):
        # 创建 mock StageRuntime 实例
        s1_runtime = create_mock_stage_runtime("s1", "func1", "serial", "serial")
        s2_runtime = create_mock_stage_runtime("s2", "func2", "thread", "async")
        s3_runtime = create_mock_stage_runtime("s3", "func3", "serial", "serial")
        s4_runtime = create_mock_stage_runtime("s4", "func4", "thread", "thread")

        stage_runtime_dict = {
            s1_runtime.stage.get_name(): s1_runtime,
            s2_runtime.stage.get_name(): s2_runtime,
            s3_runtime.stage.get_name(): s3_runtime,
            s4_runtime.stage.get_name(): s4_runtime,
        }

        # 模拟邻接表
        out_edges = {
            s1_runtime.stage.get_name(): [s2_runtime.stage.get_name(), s3_runtime.stage.get_name()],
            s2_runtime.stage.get_name(): [s4_runtime.stage.get_name()],
            s3_runtime.stage.get_name(): [s4_runtime.stage.get_name()],
            s4_runtime.stage.get_name(): [],
        }

        # 模拟循环图
        cyclic_s1_runtime = create_mock_stage_runtime("cs1", "cfunc1", "serial", "serial")
        cyclic_s2_runtime = create_mock_stage_runtime("cs2", "cfunc2", "serial", "serial")
        cyclic_s3_runtime = create_mock_stage_runtime("cs3", "cfunc3", "serial", "serial")

        cyclic_stage_runtime_dict = {
            cyclic_s1_runtime.stage.get_name(): cyclic_s1_runtime,
            cyclic_s2_runtime.stage.get_name(): cyclic_s2_runtime,
            cyclic_s3_runtime.stage.get_name(): cyclic_s3_runtime,
        }

        cyclic_out_edges = {
            cyclic_s1_runtime.stage.get_name(): [cyclic_s2_runtime.stage.get_name()],
            cyclic_s2_runtime.stage.get_name(): [cyclic_s3_runtime.stage.get_name()],
            cyclic_s3_runtime.stage.get_name(): [cyclic_s1_runtime.stage.get_name()],
        }

        return {
            "s1": s1_runtime.stage,
            "s2": s2_runtime.stage,
            "s3": s3_runtime.stage,
            "s4": s4_runtime.stage,
            "stage_runtime_dict": stage_runtime_dict,
            "out_edges": out_edges,
            "cyclic_s1": cyclic_s1_runtime.stage,
            "cyclic_stage_runtime_dict": cyclic_stage_runtime_dict,
            "cyclic_out_edges": cyclic_out_edges,
        }

    def test_build_structure_graph_dag(self, mock_graph_data):
        """测试 DAG 图结构构建"""
        s1 = mock_graph_data["s1"]
        stage_runtime_dict = mock_graph_data["stage_runtime_dict"]
        out_edges = mock_graph_data["out_edges"]

        graphs = build_structure_graph([s1], out_edges, stage_runtime_dict)
        assert len(graphs) == 1
        graph = graphs[0]

        assert graph["name"] == "s1"
        assert len(graph["next_stages"]) == 2
        assert graph["next_stages"][0]["name"] == "s2"
        assert graph["next_stages"][1]["name"] == "s3"
        assert graph["next_stages"][0]["next_stages"][0]["name"] == "s4"
        assert graph["next_stages"][1]["next_stages"][0]["name"] == "s4"
        assert graph["next_stages"][1]["next_stages"][0]["is_ref"] is True # s4 被 s2 和 s3 引用，第二次出现应为 is_ref

    def test_build_structure_graph_cyclic(self, mock_graph_data):
        """测试循环图结构构建，is_ref 标记应正确"""
        cs1 = mock_graph_data["cyclic_s1"]
        cyclic_stage_runtime_dict = mock_graph_data["cyclic_stage_runtime_dict"]
        cyclic_out_edges = mock_graph_data["cyclic_out_edges"]

        graphs = build_structure_graph([cs1], cyclic_out_edges, cyclic_stage_runtime_dict)
        assert len(graphs) == 1
        graph = graphs[0]

        assert graph["name"] == "cs1"
        assert graph["next_stages"][0]["name"] == "cs2"
        assert graph["next_stages"][0]["next_stages"][0]["name"] == "cs3"
        assert graph["next_stages"][0]["next_stages"][0]["next_stages"][0]["name"] == "cs1"
        assert graph["next_stages"][0]["next_stages"][0]["next_stages"][0]["is_ref"] is True # 循环引用

    def test_format_structure_list_from_graph(self, mock_graph_data):
        """测试 JSON 图结构到格式化文本的转换"""
        s1 = mock_graph_data["s1"]
        stage_runtime_dict = mock_graph_data["stage_runtime_dict"]
        out_edges = mock_graph_data["out_edges"]

        graphs = build_structure_graph([s1], out_edges, stage_runtime_dict)
        formatted_list = format_structure_list_from_graph(graphs)

        assert len(formatted_list) > 0
        # assert "s1::<lambda> (S:serial, E:serial, W:20)" in formatted_list[1]
        assert any("[Ref]" in line for line in formatted_list)
