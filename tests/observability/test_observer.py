import io
from contextlib import redirect_stderr, redirect_stdout

import pytest

from celestialflow import Observer, ObserverHub, PrintObserver, TaskExecutor, TaskGraph
from celestialflow.observability import (
    NodeEndEvent,
    NodeStartEvent,
    TaskFailEvent,
    TaskInputEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
)
from celestialflow.runtime.util_errors import ConfigurationError


# =========================
# 快速测试函数（无副作用）
# =========================
def add_one(x):
    """测试用同步加一函数。"""
    return x + 1


def double(x):
    """测试用同步乘二函数。"""
    return x * 2


def raise_on_negative(x):
    """测试用函数，负数时抛出异常。"""
    if x < 0:
        raise ValueError(f"negative value: {x}")
    return x * 10


class RecordingObserver(Observer):
    """记录收到的全部事件。"""

    def __init__(self):
        """初始化事件记录列表。"""
        self.events = []

    def on_node_start(self, event: NodeStartEvent) -> None:
        """记录节点启动事件。"""
        self.events.append(event)

    def on_task_input(self, event: TaskInputEvent) -> None:
        """记录任务输入事件。"""
        self.events.append(event)

    def on_task_success(self, event: TaskSuccessEvent) -> None:
        """记录任务成功事件。"""
        self.events.append(event)

    def on_task_fail(self, event: TaskFailEvent) -> None:
        """记录任务失败事件。"""
        self.events.append(event)

    def on_task_skip(self, event: TaskSkipEvent) -> None:
        """记录任务跳过事件。"""
        self.events.append(event)

    def on_node_end(self, event: NodeEndEvent) -> None:
        """记录节点结束事件。"""
        self.events.append(event)


def _only(events, event_type):
    """筛选出指定类型的事件。"""
    return [event for event in events if isinstance(event, event_type)]


class TestExecutorObserver:
    def test_observer_receives_full_lifecycle(self):
        """observer 在执行过程中收到完整生命周期事件"""
        observer = RecordingObserver()
        executor = TaskExecutor("ObserverTest", add_one, execution_mode="serial")
        executor.add_observer(observer)
        executor.run([1, 2, 3])

        starts = _only(observer.events, NodeStartEvent)
        ends = _only(observer.events, NodeEndEvent)
        inputs = _only(observer.events, TaskInputEvent)
        successes = _only(observer.events, TaskSuccessEvent)

        assert len(starts) == 1
        assert len(ends) == 1
        assert len(inputs) == 3
        assert len(successes) == 3

        assert starts[0].node == "ObserverTest"
        assert starts[0].task_count == 3
        assert all(event.source == "external" for event in inputs)
        assert ends[0].succeeded == 3
        assert ends[0].failed == 0
        assert ends[0].skipped == 0
        assert observer.events[-1] is ends[0]

    def test_task_success_event_carries_payload_and_ids(self):
        """任务成功事件携带任务、结果与事件 ID"""
        observer = RecordingObserver()
        executor = TaskExecutor("SuccessPayload", double, execution_mode="serial")
        executor.add_observer(observer)
        executor.run([21])

        success = _only(observer.events, TaskSuccessEvent)[0]
        assert success.task == 21
        assert success.result == 42
        assert success.node == "SuccessPayload"
        assert success.task_id != success.success_id
        assert success.success_id > success.task_id

    def test_print_observer(self):
        """内置 PrintObserver 输出生命周期日志，且任务总数不重复累加"""
        observer = PrintObserver("PrintObserverTest")
        executor = TaskExecutor(
            "PrintObserverTest", raise_on_negative, execution_mode="serial"
        )
        executor.add_observer(observer)

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            executor.run([1, -1, 2])

        output = buffer.getvalue()
        assert "[PrintObserverTest] start" in output
        assert "[PrintObserverTest] finish" in output
        assert observer.total.get() == 3
        assert observer.succeeded.get() == 2
        assert observer.failed.get() == 1

    def test_observer_with_errors(self):
        """observer 收到失败事件"""

        class CountObserver(Observer):
            def __init__(self):
                """初始化成功与失败计数。"""
                self.successes = 0
                self.failures = 0

            def on_task_success(self, event: TaskSuccessEvent) -> None:
                """累计成功任务数量。"""
                self.successes += 1

            def on_task_fail(self, event: TaskFailEvent) -> None:
                """累计失败任务数量。"""
                self.failures += 1

        observer = CountObserver()
        executor = TaskExecutor(
            "ObserverErrorTest", raise_on_negative, execution_mode="serial"
        )
        executor.add_observer(observer)
        executor.run([1, -1, 2])

        assert observer.successes == 2
        assert observer.failures == 1

    def test_observer_receives_skip_callback(self):
        """observer 收到跳过任务事件"""

        class SkipObserver(Observer):
            def __init__(self):
                """初始化跳过计数。"""
                self.skipped = 0

            def on_task_skip(self, event: TaskSkipEvent) -> None:
                """累计跳过任务数量。"""
                self.skipped += 1

        observer = SkipObserver()
        executor = TaskExecutor(
            "ObserverSkipTest",
            add_one,
            execution_mode="serial",
            skip_func=lambda x: x == 0,
        )
        executor.add_observer(observer)
        executor.run([0, 1, 2])

        assert observer.skipped == 1

    def test_no_observer_works(self):
        """没有 observer 时正常运行"""
        executor = TaskExecutor("NoObserver", add_one, execution_mode="serial")
        executor.run([1, 2, 3])
        assert executor.metrics.get_counts()["tasks_succeeded"] == 3

    def test_multiple_observers(self):
        """多个 observer 同时收到回调"""

        class Counter(Observer):
            def __init__(self):
                """初始化成功计数。"""
                self.count = 0

            def on_task_success(self, event: TaskSuccessEvent) -> None:
                """累计成功回调次数。"""
                self.count += 1

        o1, o2 = Counter(), Counter()
        executor = TaskExecutor("MultiObserver", add_one, execution_mode="serial")
        executor.add_observer(o1)
        executor.add_observer(o2)
        executor.run([1, 2])

        assert o1.count == 2
        assert o2.count == 2

    def test_remove_observer(self):
        """移除 observer 后不再收到回调"""

        class Counter(Observer):
            def __init__(self):
                """初始化成功计数。"""
                self.count = 0

            def on_task_success(self, event: TaskSuccessEvent) -> None:
                """累计成功回调次数。"""
                self.count += 1

        observer = Counter()
        executor = TaskExecutor("RemoveObserver", add_one, execution_mode="serial")
        executor.add_observer(observer)
        executor.remove_observer(observer)
        executor.run([1, 2])

        assert observer.count == 0

    def test_task_input_reports_upstream_source(self):
        """上游下发的任务会触发 source='upstream' 的输入事件"""
        upstream = TaskExecutor("up", add_one)
        downstream = TaskExecutor("down", double)
        observer = RecordingObserver()
        downstream.add_observer(observer)

        graph = TaskGraph("upstream_source_graph")
        graph.set_nodes([upstream, downstream])
        graph.connect([upstream], [downstream])
        graph.run({"up": [1, 2]})

        inputs = _only(observer.events, TaskInputEvent)
        assert len(inputs) == 2
        assert all(event.node == "down" for event in inputs)
        assert all(event.source == "upstream" for event in inputs)


class TestObserverHub:
    def test_hub_explicitly_overrides_every_observer_method(self):
        """hub 必须显式实现 Observer 协议的每个方法（防止转发漂移）"""
        protocol_methods = {
            name for name in vars(Observer) if name.startswith("on_")
        }
        assert protocol_methods
        for name in protocol_methods:
            assert name in vars(ObserverHub), f"ObserverHub must override {name}"

    def test_hub_dispatches_framework_before_users(self):
        """分发顺序固定为框架 sink 在前、用户 observer 在后"""
        order = []

        class Recorder(Observer):
            def __init__(self, tag: str):
                """记录标签。"""
                self.tag = tag

            def on_node_start(self, event: NodeStartEvent) -> None:
                """记录分发顺序。"""
                order.append(self.tag)

        hub = ObserverHub()
        hub.add_framework_sink(Recorder("framework"))
        hub.add_observer(Recorder("user"))
        hub.on_node_start(NodeStartEvent("node", "serial", 1, 0))

        assert order == ["framework", "user"]

    def test_hub_isolates_observer_exception(self):
        """单个 observer 抛异常不会中断其余 observer 的分发"""

        class Boom(Observer):
            def on_task_success(self, event: TaskSuccessEvent) -> None:
                """成功回调直接抛异常。"""
                msg = "observer boom"
                raise RuntimeError(msg)

        class Counter(Observer):
            def __init__(self):
                """初始化成功计数。"""
                self.count = 0

            def on_task_success(self, event: TaskSuccessEvent) -> None:
                """累计成功回调次数。"""
                self.count += 1

        counter = Counter()
        executor = TaskExecutor("HubIsolation", add_one, execution_mode="serial")
        executor.add_observer(Boom())
        executor.add_observer(counter)

        buffer = io.StringIO()
        with redirect_stderr(buffer):
            executor.run([1, 2])

        assert counter.count == 2
        assert "observer boom" in buffer.getvalue()

    def test_hub_rejects_cyclic_registration(self):
        """hub 拒绝会形成循环引用的注册"""
        a = ObserverHub()
        b = ObserverHub()
        a.add_observer(b)

        with pytest.raises(ConfigurationError):
            b.add_observer(a)

        with pytest.raises(ConfigurationError):
            a.add_observer(a)

    def test_framework_sink_has_no_remove_api(self):
        """框架 sink 不对外暴露移除接口"""
        assert not hasattr(ObserverHub(), "remove_framework_sink")
