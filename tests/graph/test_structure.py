from celestialflow import TaskLoop, TaskStage, TaskWheel


def add_one(x):
    return x + 1


def double(x):
    return x * 2


def to_str(x):
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

        loop = TaskLoop([s1, s2, s3])
        loop.start_loop({s1.get_tag(): [1]}, put_termination_signal=True)

        analysis = loop.get_graph_analysis()
        assert analysis["isDAG"] is False

        layers = analysis["layers_dict"]
        tags = {s1.get_tag(), s2.get_tag(), s3.get_tag()}
        for layer_tags in layers.values():
            if s1.get_tag() in layer_tags:
                assert tags.issubset(set(layer_tags))
                break

    def test_loop_source_stages(self):
        """测试 TaskLoop 的源节点推导：对于纯环结构，应返回环内的一个代表节点作为注入点"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)

        loop = TaskLoop([s1, s2])
        loop.start_loop({s1.get_tag(): [1]}, put_termination_signal=True)

        sources = loop.get_source_stages()
        assert len(sources) == 1
        assert sources[0].get_tag() in {s1.get_tag(), s2.get_tag()}


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

        wheel = TaskWheel(center, [r1, r2, r3])
        wheel.set_graph_mode("thread", "serial")

        analysis = wheel.get_graph_analysis()
        assert analysis["isDAG"] is False

        layers = analysis["layers_dict"]
        assert center.get_tag() in layers[0]
        ring_tags = {r1.get_tag(), r2.get_tag(), r3.get_tag()}
        assert ring_tags.issubset(set(layers[1]))

    def test_wheel_source_stages(self):
        """测试 TaskWheel 的源节点推导：应仅返回 Center 节点作为唯一入口"""
        center = TaskStage("center", add_one)
        r1 = TaskStage("r1", double)
        r2 = TaskStage("r2", to_str)

        wheel = TaskWheel(center, [r1, r2])
        wheel.set_graph_mode("thread", "serial")

        sources = wheel.get_source_stages()
        assert len(sources) == 1
        assert sources[0].get_tag() == center.get_tag()
