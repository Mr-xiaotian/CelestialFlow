from celestialflow.graph.util_serialize import format_structure_list_from_graph

# 超过 Python 默认递归上限(~1000)，用于回归迭代版渲染逻辑
DEEP = 5000


def make_node(name: str, mode: str = "serial", workers: int = 2) -> dict[str, object]:
    """构造测试节点元信息。"""
    return {"func_name": f"f_{name}", "execution_mode": mode, "max_workers": workers}


class TestUtilSerialize:
    def test_format_structure_list_from_graph(self):
        """验证结构图能够格式化为可读的结构列表。"""
        nodes = {
            "s1": make_node("s1"),
            "s2": make_node("s2", "async"),
            "s3": make_node("s3"),
            "s4": make_node("s4", "thread"),
        }
        edges = {"s1": ["s2", "s3"], "s2": ["s4"], "s3": ["s4"], "s4": []}

        formatted_list = format_structure_list_from_graph(nodes, edges, ["s1"])

        assert len(formatted_list) > 0
        assert "s1::f_s1 (E:serial, W:2)" in formatted_list[1]
        assert any("[Ref]" in line for line in formatted_list)

    def test_format_structure_list_from_graph_no_nodes(self):
        """空结构应返回占位提示。"""
        formatted_list = format_structure_list_from_graph({}, {}, [])

        assert formatted_list == ["+ No stages defined +"]

    def test_format_structure_list_from_graph_cycle(self):
        """环图应只展开一次，重复节点标记为 [Ref]。"""
        nodes = {f"c{i}": make_node(f"c{i}") for i in range(1, 4)}
        edges = {"c1": ["c2"], "c2": ["c3"], "c3": ["c1"]}

        formatted_list = format_structure_list_from_graph(nodes, edges, ["c1"])

        joined = "\n".join(formatted_list)
        assert joined.count("c1::") == 2  # 首次展开 + [Ref] 回指
        assert "[Ref]" in joined

    def test_format_deep_chain_no_recursion_error(self):
        """深链图不应触发递归上限。"""
        nodes = {f"n{i}": make_node(f"n{i}") for i in range(DEEP)}
        edges = {f"n{i}": [f"n{i + 1}"] for i in range(DEEP - 1)}
        edges[f"n{DEEP - 1}"] = []

        formatted_list = format_structure_list_from_graph(nodes, edges, ["n0"])

        assert len(formatted_list) == DEEP + 2  # border + 节点行 + border
        assert "n0::f_n0 (E:serial, W:2)" in formatted_list[1]
        assert "n4999::f_n4999 (E:serial, W:2)" in formatted_list[-2]