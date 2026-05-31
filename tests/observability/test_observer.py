from celestialflow import TaskExecutor, BaseObserver, CallbackObserver


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


class TestExecutorObserver:
    def test_observer_lifecycle(self):
        """observer 在执行过程中收到完整生命周期回调"""

        class RecordingObserver(BaseObserver):
            def __init__(self):
                """初始化事件记录列表。"""
                self.events = []

            def on_start(self, name, total):
                """记录执行器启动事件。"""
                self.events.append(("start", name, total))

            def on_task_success(self, count=1):
                """记录任务成功事件。"""
                self.events.append(("success", count))

            def on_task_fail(self, count=1):
                """记录任务失败事件。"""
                self.events.append(("fail", count))

            def on_task_duplicate(self, count=1):
                """记录重复任务事件。"""
                self.events.append(("duplicate", count))

            def on_tasks_added(self, count):
                """记录新增任务事件。"""
                self.events.append(("added", count))

            def on_finish(self):
                """记录执行结束事件。"""
                self.events.append(("finish",))

        observer = RecordingObserver()
        executor = TaskExecutor("ObserverTest", add_one, execution_mode="serial")
        executor.add_observer(observer)
        executor.start([1, 2, 3])

        event_types = [e[0] for e in observer.events]
        assert "start" in event_types
        assert event_types.count("success") == 3
        assert event_types[-1] == "finish"

    def test_observer_with_errors(self):
        """observer 收到失败回调"""

        class CountObserver(BaseObserver):
            def __init__(self):
                """初始化成功与失败计数。"""
                self.successes = 0
                self.failures = 0

            def on_task_success(self, count=1):
                """累计成功任务数量。"""
                self.successes += count

            def on_task_fail(self, count=1):
                """累计失败任务数量。"""
                self.failures += count

        observer = CountObserver()
        executor = TaskExecutor(
            "ObserverErrorTest", raise_on_negative, execution_mode="serial"
        )
        executor.add_observer(observer)
        executor.start([1, -1, 2])

        assert observer.successes == 2
        assert observer.failures == 1

    def test_no_observer_works(self):
        """没有 observer 时正常运行"""
        executor = TaskExecutor("NoObserver", add_one, execution_mode="serial")
        executor.start([1, 2, 3])
        assert executor.get_counts()["tasks_succeeded"] == 3

    def test_multiple_observers(self):
        """多个 observer 同时收到回调"""

        class Counter(BaseObserver):
            def __init__(self):
                """初始化成功计数。"""
                self.count = 0

            def on_task_success(self, count=1):
                """累计成功回调次数。"""
                self.count += count

        o1, o2 = Counter(), Counter()
        executor = TaskExecutor("MultiObserver", add_one, execution_mode="serial")
        executor.add_observer(o1)
        executor.add_observer(o2)
        executor.start([1, 2])

        assert o1.count == 2
        assert o2.count == 2

    def test_remove_observer(self):
        """移除 observer 后不再收到回调"""

        class Counter(BaseObserver):
            def __init__(self):
                """初始化成功计数。"""
                self.count = 0

            def on_task_success(self, count=1):
                """累计成功回调次数。"""
                self.count += count

        observer = Counter()
        executor = TaskExecutor("RemoveObserver", add_one, execution_mode="serial")
        executor.add_observer(observer)
        executor.remove_observer(observer)
        executor.start([1, 2])

        assert observer.count == 0

    def test_callback_observer(self):
        """CallbackObserver 通过回调函数接收事件"""
        results = []
        observer = CallbackObserver(
            on_task_success=lambda count=1: results.append(("success", count)),
            on_finish=lambda: results.append(("finish",)),
        )
        executor = TaskExecutor("CallbackTest", add_one, execution_mode="serial")
        executor.add_observer(observer)
        executor.start([1, 2, 3])

        assert len([r for r in results if r[0] == "success"]) == 3
        assert results[-1] == ("finish",)

    def test_callback_observer_partial(self):
        """CallbackObserver 只覆写部分回调，其余走默认空实现"""
        count = []
        observer = CallbackObserver(
            on_task_fail=lambda c=1: count.append(1),
        )
        executor = TaskExecutor("CallbackPartial", add_one, execution_mode="serial")
        executor.add_observer(observer)
        executor.start([1, 2])

        assert len(count) == 0
