import pytest

from celestialflow import TaskExecutor, TaskObserver


# =========================
# 快速测试函数（无副作用）
# =========================
def add_one(x):
    return x + 1


def double(x):
    return x * 2


def raise_on_negative(x):
    if x < 0:
        raise ValueError(f"negative value: {x}")
    return x * 10


async def async_add_one(x):
    return x + 1


async def async_double(x):
    return x * 2


# =========================
# TaskExecutor 基础测试
# =========================
class TestExecutorSerial:
    def test_serial_basic(self):
        """串行模式：正常计算结果正确"""
        executor = TaskExecutor(
            "AddOneSerial", add_one, execution_mode="serial"
        )
        tasks = [1, 2, 3, 4, 5]
        executor.start(tasks)

        result_dict = executor.process_result_dict()
        assert result_dict[1] == 2
        assert result_dict[2] == 3
        assert result_dict[3] == 4
        assert result_dict[4] == 5
        assert result_dict[5] == 6

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 5
        assert counts["tasks_failed"] == 0
        assert counts["tasks_pending"] == 0

    def test_serial_with_errors(self):
        """串行模式：部分任务失败，其余成功"""
        executor = TaskExecutor(
            "RaiseOnNegativeSerial",
            raise_on_negative,
            execution_mode="serial",

        )
        tasks = [1, -1, 2, -2, 3]
        executor.start(tasks)

        result_dict = executor.process_result_dict()
        assert result_dict[1] == 10
        assert result_dict[2] == 20
        assert result_dict[3] == 30
        assert "negative value: -1" in result_dict[-1]
        assert "negative value: -2" in result_dict[-2]

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 3
        assert counts["tasks_failed"] == 2

    def test_serial_retry(self):
        """串行模式：重试机制生效"""
        call_count = 0

        def flaky(x):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RuntimeError("flaky")
            return x + 100

        executor = TaskExecutor(
            "FlakySerialRetry",
            flaky,
            execution_mode="serial",
            max_retries=2,

        )
        executor.add_retry_exceptions(RuntimeError)
        executor.start([1])

        counts = executor.get_counts()
        # 最终成功，失败计数应为 0（重试不计入最终失败）
        assert counts["tasks_succeeded"] == 1
        assert counts["tasks_failed"] == 0
        assert call_count == 3  # 1 次初始 + 2 次重试

    def test_serial_no_retry_for_unmatched_exception(self):
        """串行模式：未配置的异常类型不触发重试"""
        executor = TaskExecutor(
            "RaiseOnNegativeNoRetry",
            raise_on_negative,
            execution_mode="serial",
            max_retries=2,

        )
        # 只重试 RuntimeError，但函数抛的是 ValueError
        executor.add_retry_exceptions(RuntimeError)
        executor.start([-1])

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 0
        assert counts["tasks_failed"] == 1


class TestExecutorThread:
    def test_thread_basic(self):
        """线程模式：正常计算结果正确"""
        executor = TaskExecutor(
            "DoubleThread",
            double,
            execution_mode="thread",
            max_workers=4,

        )
        tasks = [1, 2, 3, 4, 5]
        executor.start(tasks)

        result_dict = executor.process_result_dict()
        for t in tasks:
            assert result_dict[t] == t * 2

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 5
        assert counts["tasks_failed"] == 0


class TestExecutorAsync:
    @pytest.mark.asyncio
    async def test_async_basic(self):
        """异步模式：正常计算结果正确"""
        executor = TaskExecutor(
            "AsyncAddOneExecutor",
            async_add_one,
            execution_mode="async",
            max_workers=4,

        )
        tasks = [10, 20, 30]
        await executor.start_async(tasks)

        result_dict = executor.process_result_dict()
        assert result_dict[10] == 11
        assert result_dict[20] == 21
        assert result_dict[30] == 31

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 3

    @pytest.mark.asyncio
    async def test_async_double(self):
        """异步模式：并发执行多个任务"""
        executor = TaskExecutor(
            "AsyncDoubleExecutor",
            async_double,
            execution_mode="async",
            max_workers=4,

        )
        tasks = list(range(20))
        await executor.start_async(tasks)

        result_dict = executor.process_result_dict()
        for t in tasks:
            assert result_dict[t] == t * 2


class TestExecutorDuplicateCheck:
    def test_duplicate_check_enabled(self):
        """启用去重：重复任务只执行一次"""
        executor = TaskExecutor(
            "AddOneDedupEnabled",
            add_one,
            execution_mode="serial",
            enable_duplicate_check=True,

        )
        tasks = [1, 1, 2, 2, 2, 3]
        executor.start(tasks)

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 3
        assert counts["tasks_duplicated"] == 3
        assert counts["tasks_failed"] == 0

    def test_duplicate_check_disabled(self):
        """禁用去重：重复任务全部执行"""
        executor = TaskExecutor(
            "AddOneDedupDisabled",
            add_one,
            execution_mode="serial",
            enable_duplicate_check=False,

        )
        tasks = [1, 1, 2, 2, 2, 3]
        executor.start(tasks)

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 6
        assert counts["tasks_duplicated"] == 0


class TestExecutorSuccessCache:
    def test_success_cache(self):
        """成功结果缓存：get_success_pairs 包含正确结果"""
        executor = TaskExecutor(
            "AddOneSuccessCache",
            add_one,
            execution_mode="serial",
            enable_duplicate_check=True,

        )
        executor.start([1, 2, 3])

        pairs = executor.get_success_pairs()
        result_dict = dict(pairs)
        assert result_dict[1] == 2
        assert result_dict[2] == 3
        assert result_dict[3] == 4


class TestExecutorConfig:
    def test_invalid_execution_mode(self):
        """非法 execution_mode 应抛出异常"""
        with pytest.raises(Exception):
            TaskExecutor("AddOneInvalidMode", add_one, execution_mode="invalid")

    def test_get_summary(self):
        """get_summary 返回预期字段"""
        executor = TaskExecutor(
            "AddOneSummary", add_one, execution_mode="serial"
        )
        summary = executor.get_summary()
        assert summary["name"] == "AddOneSummary"
        assert summary["func_name"] == "add_one"
        assert summary["execution_mode"] == "serial"


class TestExecutorObserver:
    def test_observer_lifecycle(self):
        """observer 在执行过程中收到完整生命周期回调"""

        class RecordingObserver(TaskObserver):
            def __init__(self):
                self.events = []

            def on_start(self, name, total):
                self.events.append(("start", name, total))

            def on_task_success(self, count=1):
                self.events.append(("success", count))

            def on_task_fail(self, count=1):
                self.events.append(("fail", count))

            def on_task_duplicate(self, count=1):
                self.events.append(("duplicate", count))

            def on_tasks_added(self, count):
                self.events.append(("added", count))

            def on_finish(self):
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

        class CountObserver(TaskObserver):
            def __init__(self):
                self.successes = 0
                self.failures = 0

            def on_task_success(self, count=1):
                self.successes += count

            def on_task_fail(self, count=1):
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

        class Counter(TaskObserver):
            def __init__(self):
                self.count = 0

            def on_task_success(self, count=1):
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

        class Counter(TaskObserver):
            def __init__(self):
                self.count = 0

            def on_task_success(self, count=1):
                self.count += count

        observer = Counter()
        executor = TaskExecutor("RemoveObserver", add_one, execution_mode="serial")
        executor.add_observer(observer)
        executor.remove_observer(observer)
        executor.start([1, 2])

        assert observer.count == 0
