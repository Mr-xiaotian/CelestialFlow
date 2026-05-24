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

import pytest

from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue
from celestialflow.runtime.core_dispatch import TaskDispatch
from celestialflow.runtime.util_types import (
    TerminationIdPool,
    TerminationSignal,
)
from celestialflow.stage import TaskExecutor


# ── 工具函数 ──────────────────────────────────────────


def _square(x: Any) -> Any:
    return x * x


async def _async_square(x: Any) -> Any:
    return x * x


def _always_fail(_x: Any) -> None:
    msg = "boom"
    raise ValueError(msg)


class _RetryTwiceThenSucceed:
    """前 2 次抛可重试异常，第 3 次返回 x * x。"""

    __name__: str = "_RetryTwiceThenSucceed"

    def __init__(self) -> None:
        self.calls: int = 0

    def __call__(self, x: Any) -> Any:
        self.calls += 1
        if self.calls < 3:
            msg = f"retry #{self.calls}"
            raise ValueError(msg)
        return x * x


class _AsyncRetryTwiceThenSucceed:
    """异步版。"""

    __name__: str = "_AsyncRetryTwiceThenSucceed"

    def __init__(self) -> None:
        self.calls: int = 0

    async def __call__(self, x: Any) -> Any:
        self.calls += 1
        if self.calls < 3:
            msg = f"retry #{self.calls}"
            raise ValueError(msg)
        return x * x


# ── ctree stub ─────────────────────────────────────────


class _CtreeStub:
    def emit(self, event: str, **kw: Any) -> int:  # noqa: ARG002
        return 42


class _DummyLogInlet:
    def __getattr__(self, _name: str) -> Any:
        return lambda *args, **kw: None  # noqa: ARG005


# ── 最小 Executor ──────────────────────────────────────


def _make_executor(
    func: Any, max_retries: int = 1, name: str = "test"
) -> TaskExecutor:
    e = TaskExecutor(name, func, max_retries=max_retries, log_level="SUCCESS")
    e.add_retry_exceptions(ValueError)
    q_in = Queue()
    q_out = Queue()
    e.task_queue = TaskInQueue(q_in, [name], name, _DummyLogInlet())  # type: ignore[assignment]
    e.result_queue = TaskOutQueue([q_out], [None], name, _DummyLogInlet())  # type: ignore[assignment]
    e.ctree_client = _CtreeStub()  # type: ignore[assignment]
    e.log_inlet = _DummyLogInlet()  # type: ignore[assignment]
    e.fail_inlet = _DummyLogInlet()  # type: ignore[assignment]
    return e


def _put(executor: TaskExecutor, *items: Any) -> None:
    for num, i in enumerate(items):
        envelope = TaskEnvelope(task=i, id=num, source="test")
        executor.task_queue.queue.put(envelope)


def _put_termination(executor: TaskExecutor, ids: list[int] | None = None) -> None:
    if ids is None:
        ids = [-1]
    executor.task_queue.queue.put(TerminationIdPool(ids))


def _collect_results(executor: TaskExecutor) -> list[Any]:
    results: list[Any] = []
    q = executor.result_queue.queue_list[0]
    while not q.empty():
        results.append(q.get())
    return results


# ── serial ─────────────────────────────────────────────


class TestDispatchSerial:
    def test_single_task(self) -> None:
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
        executor = _make_executor(_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)
        _put(executor, 1, 2, 3, 4, 5)
        _put_termination(executor)
        dispatch.dispatch_serial()
        results = _collect_results(executor)
        assert isinstance(results[-1], TerminationSignal)
        assert len(results) == 6

    def test_retry_then_succeed(self) -> None:
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
        executor = _make_executor(_always_fail, name="fail_test")
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)
        _put(executor, 42)
        _put_termination(executor)
        dispatch.dispatch_serial()
        results = _collect_results(executor)
        assert len(results) == 1
        assert isinstance(results[0], TerminationSignal)

    def test_termination_single_id(self) -> None:
        executor = _make_executor(_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)
        _put(executor, 1, 2)
        _put_termination(executor, ids=[99])
        dispatch.dispatch_serial()
        results = _collect_results(executor)
        assert len(results) == 3
        assert isinstance(results[-1], TerminationSignal)

    def test_termination_multi_id(self) -> None:
        executor = _make_executor(_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)
        _put_termination(executor, ids=[1, 2, 3])
        dispatch.dispatch_serial()
        results = _collect_results(executor)
        assert len(results) == 1
        assert isinstance(results[0], TerminationSignal)


# ── thread ─────────────────────────────────────────────


class TestDispatchThread:
    def test_basic_parallel(self) -> None:
        executor = _make_executor(_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=4)
        _put(executor, *range(10))
        _put_termination(executor)
        dispatch.dispatch_thread()
        results = _collect_results(executor)
        task_results = [r for r in results if not isinstance(r, TerminationSignal)]
        assert len(task_results) == 10
        assert dispatch._pool is None

    def test_thread_duplicate(self) -> None:
        executor = _make_executor(_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=2)
        executor.task_queue.queue.put(TaskEnvelope(task=7, id=1, source="test"))
        executor.task_queue.queue.put(TaskEnvelope(task=7, id=2, source="test"))
        executor.task_queue.queue.put(TaskEnvelope(task=3, id=3, source="test"))
        _put_termination(executor)
        dispatch.dispatch_thread()
        results = _collect_results(executor)
        task_results = [r for r in results if not isinstance(r, TerminationSignal)]
        assert len(task_results) >= 1
        assert executor.metrics.get_duplicate_count() == 1


# ── async ──────────────────────────────────────────────


class TestDispatchAsync:
    def test_basic_async(self) -> None:
        executor = _make_executor(_async_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=4)

        async def _run() -> list[Any]:
            _put(executor, *range(10))
            _put_termination(executor)
            await dispatch.dispatch_async()
            return _collect_results(executor)

        results = asyncio.run(_run())
        task_results = [r for r in results if not isinstance(r, TerminationSignal)]
        assert len(task_results) == 10

    def test_async_retry_then_succeed(self) -> None:
        func = _AsyncRetryTwiceThenSucceed()
        executor = _make_executor(func, max_retries=2, name="async_retry")
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)

        async def _run() -> None:
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
        executor = _make_executor(_square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)

        def _run() -> None:
            _put_termination(executor)
            if mode == "serial":
                dispatch.dispatch_serial()
            elif mode == "thread":
                dispatch.dispatch_thread()
            else:

                async def _a() -> None:
                    await dispatch.dispatch_async()

                asyncio.run(_a())

        _run()
        results = _collect_results(executor)
        assert len(results) == 1
        assert isinstance(results[0], TerminationSignal)

    @pytest.mark.parametrize("mode", ["serial", "thread", "async"])
    def test_result_count(self, mode: str) -> None:
        executor = _make_executor(_async_square if mode == "async" else _square)
        dispatch = TaskDispatch(executor, executor.func, max_workers=1)

        def _run() -> None:
            _put(executor, 1, 2, 3, 4, 5)
            _put_termination(executor)
            if mode == "serial":
                dispatch.dispatch_serial()
            elif mode == "thread":
                dispatch.dispatch_thread()
            else:

                async def _a() -> None:
                    await dispatch.dispatch_async()

                asyncio.run(_a())

        _run()
        results = _collect_results(executor)
        task_results = [r for r in results if not isinstance(r, TerminationSignal)]
        assert len(task_results) == 5
