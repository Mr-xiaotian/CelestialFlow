from celestialflow.graph.util_serialize import format_structure_list_from_graph


class TestUtilSerialize:
    def test_format_structure_list_from_graph(self):
        """验证结构图能够格式化为可读的结构列表。"""
        nodes = {
            "s1": {
                "func_name": "<lambda>",
                "execution_mode": "serial",
                "max_workers": 2,
            },
            "s2": {
                "func_name": "<lambda>",
                "execution_mode": "async",
                "max_workers": 2,
            },
            "s3": {
                "func_name": "<lambda>",
                "execution_mode": "serial",
                "max_workers": 2,
            },
            "s4": {
                "func_name": "<lambda>",
                "execution_mode": "thread",
                "max_workers": 2,
            },
        }
        edges = {"s1": ["s2", "s3"], "s2": ["s4"], "s3": ["s4"], "s4": []}

        formatted_list = format_structure_list_from_graph(nodes, edges, ["s1"])

        assert len(formatted_list) > 0
        assert "s1::<lambda> (E:serial, W:2)" in formatted_list[1]
        assert any("[Ref]" in line for line in formatted_list)

    def test_format_structure_list_from_graph_no_nodes(self):
        """空结构应返回占位提示。"""
        formatted_list = format_structure_list_from_graph({}, {}, [])

        assert formatted_list == ["+ No stages defined +"]