"""TaskDispatch 核心调度器测试。

覆盖 serial/thread/async 三种 dispatch 模式的核心路径：
- 正常任务顺利执行
- 异常重试（成功 / 耗尽）
- 终止信号合并与退出
"""

from __future__ import annotations

import asyncio
from queue import Queue
from typing import Any
from weakref import WeakKeyDictionary

import pytest

from celestialflow.observer import (
    Observer,
    TaskFailEvent,
    TaskInputEvent,
    TaskRetryEvent,
    WorkerCrashEvent,
)
from celestialflow.persist import LifecycleInlet, LifecycleSpout
from celestialflow.reporter import MetricsObserver
from celestialflow.runtime import TaskEnvelope
from celestialflow.runtime.util_types import TerminationSignal
from celestialflow.node import TaskExecutor
from celestialflow.node.core_dispatch import TaskDispatch
from conftest import wait_until

_RESULT_COLLECTORS: WeakKeyDictionary[TaskExecutor, Queue[Any]] = WeakKeyDictionary()


# ── 工具函数 ──────────────────────────────────────────


def _square(x: Any) -> Any:
    """测试用同步平方函数。"""
    return x * x


async def _async_square(x: Any) -> Any:
    """测试用异步平方函数。"""
    return x * x


async def _async_always_fail(_x: Any) -> None:
    """测试用异步函数，始终抛出异常。"""
    msg = "async boom"
    raise ValueError(msg)


def _always_fail(_x: Any) -> None:
    """测试用函数，始终抛出异常。"""
    msg = "boom"
    raise ValueError(msg)


class _RetryTwiceThenSucceed:
    """前 2 次抛可重试异常，第 3 次返回 x * x。"""

    __name__: str = "_RetryTwiceThenSucceed"

    def __init__(self) -> None:
        """初始化重试计数器。"""
        self.calls: int = 0

    def __call__(self, x: Any) -> Any:
        """前两次抛错，第三次返回平方结果。"""
        self.calls += 1
        if self.calls < 3:
            msg = f"retry #{self.calls}"
            raise ValueError(msg)
        return x * x


class _AsyncRetryTwiceThenSucceed:
    """异步版。"""

    __name__: str = "_AsyncRetryTwiceThenSucceed"

    def __init__(self) -> None:
        """初始化异步重试计数器。"""
        self.calls: int = 0

    async def __call__(self, x: Any) -> Any:
        """前两次异步抛错，第三次返回平方结果。"""
        self.calls += 1
        if self.calls < 3:
            msg = f"retry #{self.calls}"
            raise ValueError(msg)
        return x * x


# ── ctree stub ─────────────────────────────────────────


class _CtreeStub:
    def __init__(self, start_id: int = 42) -> None:
        """使用递增事件 ID，避免与 sqlite 唯一约束冲突。"""
        self._next_id = start_id

    def emit(self, event: str, **kw: Any) -> int:
        """返回递增事件 ID 以替代真实 ctree。"""
        current_id = self._next_id
        self._next_id += 1
        return current_id


# ── 最小 Executor ──────────────────────────────────────


def _make_executor(
    func: Any,
    max_retries: int = 1,
    name: str = "test",
) -> TaskExecutor:
    """构造最小可运行的测试执行器。"""
    e = TaskExecutor(
        name,
        func,
        max_retries=max_retries,
    )
    e.set_retry_exceptions(ValueError)
    e.ctree_client = _CtreeStub()
    # 模拟 node.run 路径：注册单节点指标观察者，使指标随事件更新。
    metrics_observer = MetricsObserver()
    e.metrics = metrics_observer
    e.observers.add_observer(metrics_observer)
    metrics_observer.on_node_added(e.get_name())
    # 通过公开 API 为测试注册结果收集队列，避免向 executor 注入测试专用属性。
    collector: Queue[Any] = Queue()
    e.yield_queue.add_queue("test_collector", collector)
    _RESULT_COLLECTORS[e] = collector
    return e


def _put(executor: TaskExecutor, *items: Any) -> None:
    """向执行器输入队列写入任务信封。"""
    for num, i in enumerate(items):
        envelope = TaskEnvelope(task=i, id=num)
        executor.task_queue.put(envelope)


def _put_termination(executor: TaskExecutor, ids: list[int] | None = None) -> None:
    """发送终止信号，让框架通过 _merge_termination() 自然合并后退出调度循环。

    使用公开 API put()，注入 TerminationSignal（而非直接操作内部 TerminationIdPool）。
    """
    if ids is None:
        ids = [-1]
    # 使用 source="input" 触发直接退出路径，source_names 为空的单 executor 场景与之兼容
    executor.task_queue.put(TerminationSignal(_id=ids[0], source="input"))


def _collect_results(executor: TaskExecutor) -> list[Any]:
    """收集执行器结果队列中的全部结果。"""
    results: list[Any] = []
    q = _RESULT_COLLECTORS[executor]
    while not q.empty():
        results.append(q.get())
    return results


# ── serial ─────────────────────────────────────────────


class TestDispatchSerial:
    def test_single_task(self) -> None:
        """验证串行模式能处理单个任务。"""
        executor = _make_executor(_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)
        _put(executor, 3)
        _put_termination(executor)
        dispatch.dispatch_serial()
        results = _collect_results(executor)
        assert isinstance(results[-1], TerminationSignal)
        task_results = results[:-1]
        assert len(task_results) == 1
        assert task_results[0].get_task() == 9

    def test_multiple_tasks(self) -> None:
        """验证串行模式能处理多个任务。"""
        executor = _make_executor(_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)
        _put(executor, 1, 2, 3, 4, 5)
        _put_termination(executor)
        dispatch.dispatch_serial()
        results = _collect_results(executor)
        assert isinstance(results[-1], TerminationSignal)
        assert len(results) == 6

    def test_retry_then_succeed(self) -> None:
        """验证串行模式下任务重试后最终成功。"""
        func = _RetryTwiceThenSucceed()
        executor = _make_executor(func, max_retries=2, name="retry_test")
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)
        _put(executor, 5)
        _put_termination(executor)
        dispatch.dispatch_serial()
        results = _collect_results(executor)
        task_results = [r for r in results if not isinstance(r, TerminationSignal)]
        assert len(task_results) == 1
        assert task_results[0].get_task() == 25
        assert func.calls == 3

    def test_retry_exhausted(self) -> None:
        """验证串行模式下重试耗尽后仅输出终止信号。"""
        executor = _make_executor(_always_fail, name="fail_test")
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)
        _put(executor, 42)
        _put_termination(executor)
        dispatch.dispatch_serial()
        results = _collect_results(executor)
        assert len(results) == 1
        assert isinstance(results[0], TerminationSignal)

    def test_termination_single_id(self) -> None:
        """验证单个终止 ID 能正确传递到结果队列。"""
        executor = _make_executor(_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)
        _put(executor, 1, 2)
        _put_termination(executor, ids=[99])
        dispatch.dispatch_serial()
        results = _collect_results(executor)
        assert len(results) == 3
        assert isinstance(results[-1], TerminationSignal)

    def test_termination_multi_id(self) -> None:
        """验证多个终止 ID 合并后仍只输出一个终止信号。"""
        executor = _make_executor(_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)
        _put_termination(executor, ids=[1, 2, 3])
        dispatch.dispatch_serial()
        results = _collect_results(executor)
        assert len(results) == 1
        assert isinstance(results[0], TerminationSignal)

    def test_success_fanout_creates_distinct_downstream_ids(self) -> None:
        """普通 executor 成功后应为每个真实下游创建独立任务 ID。"""

        class _SequentialCtreeStub:
            def __init__(self) -> None:
                self._next_id = 100

            def emit(self, event: str, **kw: Any) -> int:
                current_id = self._next_id
                self._next_id += 1
                return current_id

        executor = _make_executor(_square)
        executor.ctree_client = _SequentialCtreeStub()
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)
        collector_a: Queue[Any] = Queue()
        collector_b: Queue[Any] = Queue()
        # 模拟 ``connect_to`` 的绑定行为：注册下游队列
        executor.yield_queue.add_queue("downstream_a", collector_a)
        executor.yield_queue.add_queue("downstream_b", collector_b)

        # 直接驱动 dispatch（不经过 node.run），因此手动装配 lifecycle 持久化。
        lifecycle_spout = LifecycleSpout()
        lifecycle_observer = LifecycleInlet().bind_spout(lifecycle_spout)
        executor.add_observer(lifecycle_observer)
        lifecycle_spout.start()
        executor._lifecycle_db_path = lifecycle_spout.db_path
        try:
            lifecycle_observer.on_task_input(
                TaskInputEvent(executor.get_name(), 3, "(3)", 0, "external")
            )
            _put(executor, 3)
            _put_termination(executor)
            dispatch.dispatch_serial()

            item_a = collector_a.get()
            item_b = collector_b.get()

            assert isinstance(item_a, TaskEnvelope)
            assert isinstance(item_b, TaskEnvelope)
            assert item_a.get_task() == 9
            assert item_b.get_task() == 9
            assert item_a.get_id() != item_b.get_id()
            wait_until(
                lambda: executor.get_success_pairs() == [(3, 9)],
                message="timeout waiting for lifecycle store to persist success result",
            )
            assert executor.get_success_pairs() == [(3, 9)]
        finally:
            lifecycle_spout.stop()


# ── thread ─────────────────────────────────────────────


class TestDispatchThread:
    def test_basic_parallel(self) -> None:
        """验证线程模式能并行处理一批任务。"""
        executor = _make_executor(_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=4)
        _put(executor, *range(10))
        _put_termination(executor)
        dispatch.dispatch_thread()
        results = _collect_results(executor)
        task_results = [r for r in results if not isinstance(r, TerminationSignal)]
        assert len(task_results) == 10


# ── async ──────────────────────────────────────────────


class TestDispatchAsync:
    def test_basic_async(self) -> None:
        """验证异步模式能处理一批任务。"""
        executor = _make_executor(_async_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=4)

        async def _run() -> list[Any]:
            """执行异步调度并返回收集到的结果。"""
            _put(executor, *range(10))
            _put_termination(executor)
            await dispatch.dispatch_async()
            return _collect_results(executor)

        results = asyncio.run(_run())
        task_results = [r for r in results if not isinstance(r, TerminationSignal)]
        assert len(task_results) == 10

    def test_async_retry_then_succeed(self) -> None:
        """验证异步模式下任务重试后最终成功。"""
        func = _AsyncRetryTwiceThenSucceed()
        executor = _make_executor(func, max_retries=2, name="async_retry")
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)

        async def _run() -> None:
            """执行异步重试场景。"""
            _put(executor, 5)
            _put_termination(executor)
            await dispatch.dispatch_async()

        asyncio.run(_run())
        results = _collect_results(executor)
        task_results = [r for r in results if not isinstance(r, TerminationSignal)]
        assert len(task_results) == 1
        assert func.calls == 3


# ── 参数化 ──────────────────────────────────────────────


# ── worker 崩溃兜底 ────────────────────────────────────


class _CrashOnFailObserver(Observer):
    """``on_task_fail`` 抛异常，用于验证 hub 的异常隔离。"""

    def __init__(self) -> None:
        """初始化调用计数。"""
        self.calls = 0

    def on_task_fail(self, event: TaskFailEvent) -> None:
        """失败回调，累加计数后抛出异常。"""
        self.calls += 1
        msg = "observer boom"
        raise RuntimeError(msg)


class _RecordingCrashObserver(Observer):
    """记录 ``on_worker_crash`` 事件。"""

    def __init__(self) -> None:
        """初始化崩溃记录列表。"""
        self.crashes: list[Exception] = []

    def on_worker_crash(self, event: WorkerCrashEvent) -> None:
        """记录崩溃异常。"""
        self.crashes.append(event.exception)


class _CrashOnRetryObserver(Observer):
    """``on_task_retry`` 抛异常，用于验证 hub 的异常隔离。"""

    def __init__(self) -> None:
        """初始化调用计数。"""
        self.calls = 0

    def on_task_retry(self, event: TaskRetryEvent) -> None:
        """重试回调，累加计数后抛出异常。"""
        self.calls += 1
        msg = "retry observer boom"
        raise RuntimeError(msg)


def _run_dispatch(dispatch: TaskDispatch[Any, Any], mode: str) -> None:
    """按模式运行调度器。"""
    if mode == "serial":
        dispatch.dispatch_serial()
    elif mode == "thread":
        dispatch.dispatch_thread()
    else:

        async def _run_async() -> None:
            """执行异步调度分支。"""
            await dispatch.dispatch_async()

        asyncio.run(_run_async())


class TestWorkerCrashKeepsTerminationSignal:
    """回归测试：失败/重试处理链自身崩溃时，终止信号仍必须发出。"""

    @pytest.mark.parametrize("mode", ["serial", "thread", "async"])
    def test_fail_handler_crash_keeps_termination(
        self, mode: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """失败处理链中 observer 抛异常时，异常被 hub 隔离，
        终止信号照常发出，不触发 ``worker_crash``。"""
        executor = _make_executor(
            _async_always_fail if mode == "async" else _always_fail,
            max_retries=0,
            name="crash_fail",
        )
        observer = _CrashOnFailObserver()
        executor.add_observer(observer)
        recording = _RecordingCrashObserver()
        executor.add_observer(recording)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)

        _put(executor, 42)
        _put_termination(executor)
        _run_dispatch(dispatch, mode)

        # 异常在 observer hub 层被隔离，不应到达 worker_crash
        assert observer.calls == 1
        assert len(recording.crashes) == 0

        results = _collect_results(executor)
        assert len(results) == 1
        assert isinstance(results[0], TerminationSignal)
        assert executor.metrics.get_node_metrics(executor.get_name()).failed == 1

    @pytest.mark.parametrize("mode", ["serial", "thread", "async"])
    def test_retry_handler_crash_keeps_termination(
        self, mode: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """重试回调抛异常时，异常被 hub 隔离，调度继续直到重试耗尽，
        终止信号照常发出，不触发 ``worker_crash``。"""
        executor = _make_executor(
            _async_always_fail if mode == "async" else _always_fail,
            max_retries=1,
            name="crash_retry",
        )
        observer = _CrashOnRetryObserver()
        executor.add_observer(observer)
        recording = _RecordingCrashObserver()
        executor.add_observer(recording)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)

        _put(executor, 42)
        _put_termination(executor)
        _run_dispatch(dispatch, mode)

        results = _collect_results(executor)
        assert len(results) == 1
        assert isinstance(results[0], TerminationSignal)
        assert observer.calls == 1
        assert len(recording.crashes) == 0
        # 重试后仍失败，最终计入一次失败
        assert executor.metrics.get_node_metrics(executor.get_name()).failed == 1

class TestDispatchCoreBehavior:
    @pytest.mark.parametrize("mode", ["serial", "thread", "async"])
    def test_empty_queue_with_termination(self, mode: str) -> None:
        """验证空队列在收到终止信号后可正常退出。"""
        executor = _make_executor(_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)

        def _run() -> None:
            """按当前模式运行空队列终止场景。"""
            _put_termination(executor)
            if mode == "serial":
                dispatch.dispatch_serial()
            elif mode == "thread":
                dispatch.dispatch_thread()
            else:

                async def _a() -> None:
                    """执行异步调度分支。"""
                    await dispatch.dispatch_async()

                asyncio.run(_a())

        _run()
        results = _collect_results(executor)
        assert len(results) == 1
        assert isinstance(results[0], TerminationSignal)

    @pytest.mark.parametrize("mode", ["serial", "thread", "async"])
    def test_result_count(self, mode: str) -> None:
        """验证不同调度模式下结果数量一致。"""
        executor = _make_executor(_async_square if mode == "async" else _square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)

        def _run() -> None:
            """按当前模式运行多任务场景。"""
            _put(executor, 1, 2, 3, 4, 5)
            _put_termination(executor)
            if mode == "serial":
                dispatch.dispatch_serial()
            elif mode == "thread":
                dispatch.dispatch_thread()
            else:

                async def _a() -> None:
                    """执行异步调度分支。"""
                    await dispatch.dispatch_async()

                asyncio.run(_a())

        _run()
        results = _collect_results(executor)
        task_results = [r for r in results if not isinstance(r, TerminationSignal)]
        assert len(task_results) == 5
