from __future__ import annotations

import sqlite3
from queue import Empty

import pytest

from celestialflow import TaskExecutor
from celestialflow.persistence import (
    close_funnel,
    get_lifecycle_spout,
    get_log_spout,
    open_funnel,
)


def add_one(x: int) -> int:
    """测试用同步加一函数。"""
    return x + 1


@pytest.fixture(autouse=True)
def _cleanup_global_spouts() -> None:
    """为每个用例清理全局 spout，避免后台线程与文件状态串扰。"""
    _reset_spout(get_log_spout())
    _reset_spout(get_lifecycle_spout())
    yield
    _reset_spout(get_log_spout())
    _reset_spout(get_lifecycle_spout())


def _reset_spout(spout) -> None:
    """停止并清空全局 spout，避免历史队列记录污染当前用例。"""
    spout.stop()
    while True:
        try:
            _ = spout.get_queue().get_nowait()
        except Empty:
            break

    counter = spout.get_counter()
    while counter.get_count() > 0:
        counter.decrement()


class TestFunnelLifecycle:
    def test_open_and_close_funnel(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """`open_funnel()` / `close_funnel()` 应启停全局 log/lifecycle spout。"""
        monkeypatch.chdir(tmp_path)

        open_funnel()
        log_spout = get_log_spout()
        lifecycle_spout = get_lifecycle_spout()

        assert log_spout._thread is not None
        assert lifecycle_spout._thread is not None
        assert log_spout._thread.is_alive()
        assert lifecycle_spout._thread.is_alive()

        assert close_funnel() == []

        assert get_log_spout()._thread is None
        assert get_lifecycle_spout()._thread is None

    def test_funnel_is_reusable(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """`open_funnel()` / `close_funnel()` 应支持多次独立启停。"""
        monkeypatch.chdir(tmp_path)

        open_funnel()
        assert get_log_spout()._thread is not None
        close_funnel()
        assert get_log_spout()._thread is None

        open_funnel()
        assert get_lifecycle_spout()._thread is not None
        close_funnel()
        assert get_lifecycle_spout()._thread is None

    def test_close_funnel_collects_errors(self, monkeypatch: pytest.MonkeyPatch):
        """`close_funnel()` 应收集 spout 停止异常而不是直接抛出。"""

        def crash_stop() -> None:
            raise RuntimeError("log stop failed")

        monkeypatch.setattr(get_log_spout(), "stop", crash_stop)

        errors = close_funnel()

        assert [str(error) for error in errors] == ["log stop failed"]

    def test_node_run_manages_funnel_and_persists(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ):
        """节点 `run` 应自动启停 spout 并将生命周期写入 sqlite。"""
        monkeypatch.chdir(tmp_path)

        executor = TaskExecutor("scope_node", add_one, execution_mode="serial")
        executor.run([1, 2])

        assert get_log_spout()._thread is None
        assert get_lifecycle_spout()._thread is None

        lifecycle_path = get_lifecycle_spout().db_path
        log_path = get_log_spout().log_path

        assert lifecycle_path is not None
        assert log_path is not None
        assert lifecycle_path.exists()
        assert log_path.exists()

        conn = sqlite3.connect(lifecycle_path)
        try:
            rows = conn.execute(
                """
                SELECT node, status, task_json, result_json
                FROM records
                ORDER BY id ASC
                """
            ).fetchall()
        finally:
            conn.close()

        assert rows == [
            ("scope_node", "success", "1", "2"),
            ("scope_node", "success", "2", "3"),
        ]
