"""Tests for benchmark helpers."""

import pytest

from celestialflow.benchmark.util_benchmark import benchmark_graph
from celestialflow.graph import TaskGraph
from celestialflow.stage import TaskStage


def add_one(x: int) -> int:
    """测试用同步加一函数。"""
    return x + 1


async def async_add_one(x: int) -> int:
    """测试用异步加一函数。"""
    return x + 1


class TestBenchmarkGraph:
    """Tests for benchmark_graph matrix coverage."""

    @pytest.mark.asyncio
    async def test_benchmark_graph_covers_all_nine_combinations(self):
        """benchmark_graph 应返回 3×3 的完整 graph/execution 组合矩阵。"""
        sync_graph = TaskGraph("sync_graph")
        sync_graph.set_stages([TaskStage("s", add_one, execution_mode="serial")])

        async_graph = TaskGraph("async_graph", graph_mode="async")
        async_graph.set_stages(
            [TaskStage("s", async_add_one, execution_mode="async")]
        )

        result = await benchmark_graph(sync_graph, async_graph, {"s": [1, 2, 3]})

        assert result["graph_modes"] == ["serial", "thread", "async"]
        assert result["execution_modes"] == ["serial", "thread", "async"]
        assert result["sync_modes"] == ["serial", "thread"]
        assert result["async_modes"] == ["async"]
        assert len(result["use_time"]) == 3
        assert all(len(row) == 3 for row in result["use_time"])
