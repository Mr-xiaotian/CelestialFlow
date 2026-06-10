import pytest
from celestialflow import TaskGraph, TaskRouter, TaskSplitter, TaskStage
from celestialflow.runtime.util_errors import InvalidOptionError, TaskFormatError


class TestTaskSplitter:
    def test_splitter_init(self):
        """测试 TaskSplitter 的初始配置：应为串行模式且不重试"""
        splitter = TaskSplitter("Splitter")
        assert splitter.execution_mode == "serial"
        assert splitter.max_retries == 0
        assert splitter.split_counter.get() == 0

    def test_splitter_process_success(self):
        """测试 TaskSplitter 在图中：成功执行后下游应收到分裂后的独立任务"""
        def noop(x):
            """测试用原样返回函数。"""
            return x

        S = TaskSplitter("S")
        A = TaskStage("A", noop)

        graph = TaskGraph()
        graph.set_stages([S, A])
        graph.connect([S], [A])
        graph.start_graph({S.get_name(): [[1, 2, 3]]})

        assert S.split_counter.get() == 3
        assert A.get_counts()["tasks_succeeded"] == 3

    def test_splitter_allows_empty_iterable(self):
        """测试 TaskSplitter 对空可迭代任务应产生 0 个子任务，而不是抛异常"""
        def noop(x):
            return x

        S = TaskSplitter("S")
        A = TaskStage("A", noop)

        graph = TaskGraph()
        graph.set_stages([S, A])
        graph.connect([S], [A])
        graph.start_graph({S.get_name(): [[]]})

        assert S.split_counter.get() == 0
        assert A.get_counts()["tasks_succeeded"] == 0

    def test_splitter_supports_generator_input(self):
        """测试 TaskSplitter 对一次性迭代器应基于拆分结果继续分发所有子任务"""
        def noop(x):
            return x

        S = TaskSplitter("S")
        A = TaskStage("A", noop)

        graph = TaskGraph()
        graph.set_stages([S, A])
        graph.connect([S], [A])
        graph.start_graph({S.get_name(): [(i for i in [1, 2, 3])]})

        assert S.split_counter.get() == 3
        assert A.get_counts()["tasks_succeeded"] == 3

    def test_splitter_allows_constructor_split_item(self):
        """测试 TaskSplitter 可通过构造参数 split_item 注入单个子任务处理逻辑"""
        splitter = TaskSplitter[str, str]("S", split_item=lambda item: item.strip())

        assert tuple(splitter._split([" a ", " b ", " c "])) == ("a", "b", "c")


class TestTaskRouter:
    def test_router_init(self):
        """测试 TaskRouter 的初始配置：应为串行模式且不重试"""
        router = TaskRouter("Router")
        assert router.execution_mode == "serial"
        assert router.max_retries == 0
        assert router.route_counters == {}

    def test_router_route_logic(self):
        """测试 TaskRouter 的核心路由逻辑：正确解析目标名称并提取任务数据"""
        router = TaskRouter("Router")
        # 预注册 target
        router.get_binding_counter("target1")

        # 正常路由
        assert router._route(("target1", "data")) == "data"

        # 异常路由：未知 target
        with pytest.raises(InvalidOptionError):
            router._route(("unknown", "data"))

        # 异常路由：格式错误
        with pytest.raises(TaskFormatError):
            router._route("not_a_tuple")

    def test_router_process_success(self):
        """测试 TaskRouter 在图中：成功执行后任务应被正确路由到指定目标节点"""
        def noop(x):
            """测试用原样返回函数。"""
            return x

        R = TaskRouter("R")
        T1 = TaskStage("target1", noop)
        T2 = TaskStage("target2", noop)

        graph = TaskGraph()
        graph.set_stages([R, T1, T2])
        graph.connect([R], [T1, T2])
        graph.start_graph({R.get_name(): [("target1", "msg1"), ("target2", "msg2")]})

        assert R.route_counters["target1"].value == 1
        assert R.route_counters["target2"].value == 1
        assert T1.get_counts()["tasks_succeeded"] == 1
        assert T2.get_counts()["tasks_succeeded"] == 1
