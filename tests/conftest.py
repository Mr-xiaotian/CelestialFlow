from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import pytest
from dotenv import load_dotenv

from celestialflow.observer import MetricsObserver

load_dotenv()


def metrics_of(node: Any) -> MetricsObserver:
    """
    取回独立运行节点 hub 上的指标观察者。

    节点自身不再持有 ``metrics`` 字段；指标观察者由运行入口注册到 ``node.observers``，
    这里从 hub 快照中取回，供断言读取。

    :param node: 已运行的任务节点
    :return: 该节点 hub 上的指标观察者
    """
    for observer in node.observers._snapshot():
        if isinstance(observer, MetricsObserver):
            return observer
    raise AssertionError("metrics observer not registered on node hub")


def wait_until(
    condition: Callable[[], bool],
    *,
    timeout: float = 5.0,
    interval: float = 0.05,
    message: str = "condition was not satisfied in time",
) -> None:
    """轮询等待条件成立，统一测试中的后台线程同步写法。"""
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        if condition():
            return
        time.sleep(interval)

    if condition():
        return

    pytest.fail(message)


def assert_stays_true(
    condition: Callable[[], bool],
    *,
    duration: float = 0.3,
    interval: float = 0.05,
    message: str = "condition changed unexpectedly",
) -> None:
    """在一小段时间内持续验证条件保持为真。"""
    deadline = time.perf_counter() + duration
    while time.perf_counter() < deadline:
        if not condition():
            pytest.fail(message)
        time.sleep(interval)
