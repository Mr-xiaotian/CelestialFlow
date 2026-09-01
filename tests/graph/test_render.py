from celestialflow.graph.util_render import render_structure_list

# 超过 Python 默认递归上限(~1000)，用于回归迭代版渲染逻辑
DEEP = 5000


class TestUtilRender:
    def test_render_structure_list(self):
        """验证结构图能够渲染为可读的结构列表。"""
        nodes = ["s1", "s2", "s3", "s4"]
        edges = {"s1": ["s2", "s3"], "s2": ["s4"], "s3": ["s4"], "s4": []}

        rendered_list = render_structure_list(nodes, edges, ["s1"])

        assert len(rendered_list) > 0
        assert "s1" in rendered_list[1]
        assert any("[Ref]" in line for line in rendered_list)

    def test_render_structure_list_no_nodes(self):
        """空结构应返回占位提示。"""
        rendered_list = render_structure_list([], {}, [])

        assert rendered_list == ["+ No stages defined +"]

    def test_render_structure_list_cycle(self):
        """环图应只展开一次，重复节点标记为 [Ref]。"""
        nodes = [f"c{i}" for i in range(1, 4)]
        edges = {"c1": ["c2"], "c2": ["c3"], "c3": ["c1"]}

        rendered_list = render_structure_list(nodes, edges, ["c1"])

        joined = "\n".join(rendered_list)
        assert joined.count("c1") == 2  # 首次展开 + [Ref] 回指
        assert "[Ref]" in joined

    def test_render_deep_chain_no_recursion_error(self):
        """深链图不应触发递归上限。"""
        nodes = [f"n{i}" for i in range(DEEP)]
        edges = {f"n{i}": [f"n{i + 1}"] for i in range(DEEP - 1)}
        edges[f"n{DEEP - 1}"] = []

        rendered_list = render_structure_list(nodes, edges, ["n0"])

        assert len(rendered_list) == DEEP + 2  # border + 节点行 + border
        assert "n0" in rendered_list[1]
        assert "n4999" in rendered_list[-2]
