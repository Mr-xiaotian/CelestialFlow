"""TaskDispatch 核心调度器测试。

覆盖 serial/thread/async 三种 dispatch 模式的核心路径：
- 正常任务顺利执行
- 异常重试（成功 / 耗尽）
- 重复任务去重
- 终止信号合并与退出
"""

from __future__ import annotations

import asyncio
from queue import Queue
from typing import Any
from weakref import WeakKeyDictionary

import pytest

from celestialflow.runtime import TaskEnvelope
from celestialflow.runtime.core_dispatch import TaskDispatch
from celestialflow.runtime.util_types import TerminationSignal
from celestialflow.stage import TaskExecutor
from tests.conftest import wait_until

_RESULT_COLLECTORS: WeakKeyDictionary[TaskExecutor, Queue[Any]] = WeakKeyDictionary()


# ── 工具函数 ──────────────────────────────────────────


def _square(x: Any) -> Any:
    """测试用同步平方函数。"""
    return x * x


async def _async_square(x: Any) -> Any:
    """测试用异步平方函数。"""
    return x * x


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

    def emit(self, event: str, **kw: Any) -> int:  # noqa: ARG002
        """返回递增事件 ID 以替代真实 ctree。"""
        current_id = self._next_id
        self._next_id += 1
        return current_id


# ── 最小 Executor ──────────────────────────────────────


def _make_executor(
    func: Any,
    max_retries: int = 1,
    name: str = "test",
    enable_duplicate_check: bool = False,
) -> TaskExecutor:
    """构造最小可运行的测试执行器。"""
    e = TaskExecutor(
        name,
        func,
        max_retries=max_retries,
        log_level="SUCCESS",
        enable_duplicate_check=enable_duplicate_check,
    )
    e.set_retry_exceptions(ValueError)
    e.init_env()
    e.ctree_client = _CtreeStub()
    # 通过公开 API 为测试注册结果收集队列，避免向 executor 注入测试专用属性
    collector: Queue[Any] = Queue()
    e.result_queue.add_queue(collector, name="test_collector")
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
        assert task_results[0].task == 9

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
        assert task_results[0].task == 25
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

    def test_success_fanout_creates_distinct_downstream_input_ids(self) -> None:
        """普通 executor 成功后应为每个真实下游创建独立 input_id。"""

        class _SequentialCtreeStub:
            def __init__(self) -> None:
                self._next_id = 100

            def emit(self, event: str, **kw: Any) -> int:  # noqa: ARG002
                current_id = self._next_id
                self._next_id += 1
                return current_id

        executor = _make_executor(_square)
        executor.persist_result = True
        executor.ctree_client = _SequentialCtreeStub()
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)
        collector_a: Queue[Any] = Queue()
        collector_b: Queue[Any] = Queue()
        executor.result_queue.add_queue(collector_a, name="downstream_a")
        executor.result_queue.add_queue(collector_b, name="downstream_b")

        executor.fallback_inlet.task_in(executor.get_name(), 0, 3)
        _put(executor, 3)
        _put_termination(executor)
        dispatch.dispatch_serial()

        item_a = collector_a.get()
        item_b = collector_b.get()

        assert isinstance(item_a, TaskEnvelope)
        assert isinstance(item_b, TaskEnvelope)
        assert item_a.task == 9
        assert item_b.task == 9
        assert item_a.id != item_b.id
        wait_until(
            lambda: executor.get_success_pairs() == [(3, 9)],
            message="timeout waiting for fallback store to persist success result",
        )
        assert executor.get_success_pairs() == [(3, 9)]


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

    def test_thread_duplicate(self) -> None:
        """验证线程模式会统计重复任务。"""
        executor = _make_executor(_square, enable_duplicate_check=True)
        dispatch = TaskDispatch(executor, executor.func, max_workers=2)
        executor.task_queue.put(TaskEnvelope(task=7, id=1))
        executor.task_queue.put(TaskEnvelope(task=7, id=2))
        executor.task_queue.put(TaskEnvelope(task=3, id=3))
        _put_termination(executor)
        dispatch.dispatch_thread()
        results = _collect_results(executor)
        task_results = [r for r in results if not isinstance(r, TerminationSignal)]
        assert len(task_results) >= 1
        assert executor.metrics.get_duplicate_count() == 1


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
