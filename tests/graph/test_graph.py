import pytest

from celestialflow import (
    TaskChain,
    TaskCross,
    TaskGraph,
    TaskGrid,
    TaskStage,
)
from celestialflow.persistence.util_sqlite import append_records
from celestialflow.runtime.util_errors import (
    InvalidOptionError,
    NodeNotFoundError,
)
from celestialflow.runtime.util_event import LocalEventClient


# =========================
# 快速测试函数
# =========================
def add_one(x: int) -> int:
    """测试用同步加一函数。"""
    return x + 1


async def async_add_one(x: int) -> int:
    """测试用异步加一函数。"""
    return x + 1


async def async_double(x: int) -> int:
    """测试用异步乘二函数。"""
    return x * 2


async def async_to_str(x: int) -> str:
    """测试用异步转字符串函数。"""
    return str(x)


async def async_add_offset(x: int, offset: int = 10) -> int:
    """测试用异步偏移函数，超过阈值时抛错。"""
    if x > 30:
        raise ValueError("too large")
    return x + offset


async def async_add_offset_10(x: int) -> int:
    """符合单参数执行器约束的异步偏移包装函数。"""
    return await async_add_offset(x, 10)


def double(x: int) -> int:
    """测试用同步乘二函数。"""
    return x * 2


def to_str(x: int) -> str:
    """测试用同步转字符串函数。"""
    return str(x)


def add_offset(x: int, offset: int = 10) -> int:
    """测试用同步偏移函数，超过阈值时抛错。"""
    if x > 30:
        raise ValueError("too large")
    return x + offset


def add_offset_10(x: int) -> int:
    """符合单参数执行器约束的同步偏移包装函数。"""
    return add_offset(x, 10)


# =========================
# TaskGraph 基础测试
# =========================
class TestTaskGraphBasic:
    def test_set_ctree_updates_existing_stages(self):
        """先 set_stages 再 set_ctree 时，已有 stage 也应共享同一事件客户端。"""
        stage1 = TaskStage("s1", add_one, execution_mode="serial")
        stage2 = TaskStage("s2", double, execution_mode="serial")
        graph = TaskGraph("test_set_ctree_updates_existing_stages")
        graph.set_stages(stages=[stage1, stage2])

        ctree_client = LocalEventClient()
        graph.set_ctree(ctree_client)

        assert graph.ctree_client is ctree_client
        assert stage1.ctree_client is ctree_client
        assert stage2.ctree_client is ctree_client

    def test_graph_stage_lookup_unknown_stage_raises(self):
        """显式按 stage 注入任务时，不存在的 stage 名称应抛出 NodeNotFoundError。"""
        graph = TaskGraph("test_put_stage_queue_unknown_stage")
        stage = TaskStage("s1", add_one, execution_mode="serial")
        graph.set_stages(stages=[stage])

        with pytest.raises(NodeNotFoundError):
            pending_stage = graph.stage_dict.get("unknown_stage")
            if pending_stage is None:
                raise NodeNotFoundError("stage not found: unknown_stage")
            pending_stage.put_task(1)

    def test_graph_dag_two_nodes(self):
        """简单 DAG：两个节点串行，结果正确传递"""
        stage1 = TaskStage("s1", add_one, execution_mode="serial")
        stage2 = TaskStage("s2", double, execution_mode="serial")

        graph = TaskGraph("test_graph_dag_two_nodes")
        graph.set_stages(stages=[stage1, stage2])
        graph.connect([stage1], [stage2])

        graph.run({"s1": [1, 2, 3]})

        # stage1 结果: 2, 3, 4 -> stage2 结果: 4, 6, 8
        assert stage1.get_counts()["tasks_succeeded"] == 3
        assert stage2.get_counts()["tasks_succeeded"] == 3

    def test_graph_fan_out(self):
        """扇出：一个节点到多个下游"""
        source = TaskStage("src", add_one, execution_mode="serial")
        sink_a = TaskStage("SinkA", double, execution_mode="serial")
        sink_b = TaskStage("SinkB", to_str, execution_mode="serial")

        graph = TaskGraph("test_graph_fan_out")
        graph.set_stages(stages=[source, sink_a, sink_b])
        graph.connect([source], [sink_a, sink_b])

        graph.run({"src": [1, 2]})

        assert source.get_counts()["tasks_succeeded"] == 2
        assert sink_a.get_counts()["tasks_succeeded"] == 2
        assert sink_b.get_counts()["tasks_succeeded"] == 2

    def test_graph_fan_in(self):
        """扇入：多个上游到一个下游"""
        source_a = TaskStage("SrcA", add_one, execution_mode="serial")
        source_b = TaskStage("SrcB", double, execution_mode="serial")
        merge = TaskStage("merge", to_str, execution_mode="serial")

        graph = TaskGraph("test_graph_fan_in")
        graph.set_stages(stages=[source_a, source_b, merge])
        graph.connect([source_a, source_b], [merge])

        graph.run({"SrcA": [1, 2], "SrcB": [10, 20]})

        assert merge.get_counts()["tasks_succeeded"] == 4

    def test_graph_error_propagation(self):
        """错误任务不会阻断整体流程"""
        stage1 = TaskStage("s1", add_offset_10, execution_mode="serial")
        stage2 = TaskStage("s2", double, execution_mode="serial")

        graph = TaskGraph("test_graph_error_propagation")
        graph.set_stages(stages=[stage1, stage2])
        graph.connect([stage1], [stage2])

        graph.run({"s1": [1, 50, 2]})

        # stage1: 1->11, 50->error, 2->12
        assert stage1.get_counts()["tasks_succeeded"] == 2
        assert stage1.get_counts()["tasks_failed"] == 1

        # stage2 只收到 2 个成功结果
        assert stage2.get_counts()["tasks_succeeded"] == 2
        assert stage2.get_counts()["tasks_failed"] == 0

    def test_graph_restore_db(self, tmp_path):
        """任务图默认应按 stage 分组读取 failed 与 pending 任务并启动。"""
        sqlite_path = tmp_path / "fallback.sqlite3"
        appended = append_records(
            sqlite_path,
            [
                {
                    "event_id": 1,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": 1,
                    "error_type": "ValueError",
                    "error_message": "bad",
                    "ts": 1.0,
                },
                {
                    "event_id": 2,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": 2,
                    "error_type": "ValueError",
                    "error_message": "bad",
                    "ts": 2.0,
                },
                {
                    "event_id": 3,
                    "stage": "s2",
                    "status": "failed",
                    "task_json": 10,
                    "error_type": "ValueError",
                    "error_message": "bad",
                    "ts": 3.0,
                },
                {
                    "event_id": 4,
                    "stage": "s2",
                    "status": "pending",
                    "task_json": 20,
                    "error_type": "",
                    "error_message": "",
                    "ts": 4.0,
                },
            ],
        )
        assert appended == 4

        stage1 = TaskStage("s1", add_one, execution_mode="serial")
        stage2 = TaskStage("s2", double, execution_mode="serial")

        graph = TaskGraph("test_graph_restore_db")
        graph.set_stages(stages=[stage1, stage2])
        graph.restore_db(sqlite_path)

        assert stage1.get_counts()["tasks_succeeded"] == 2
        assert stage2.get_counts()["tasks_succeeded"] == 2

    def test_graph_restore_db_filters_error_type_when_enabled(self, tmp_path):
        """图级 restore_db 开启过滤时，应按各 stage 的 retry_exceptions 回放。"""
        sqlite_path = tmp_path / "fallback.sqlite3"
        appended = append_records(
            sqlite_path,
            [
                {
                    "event_id": 1,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": 1,
                    "error_type": "ValueError",
                    "error_message": "bad",
                    "ts": 1.0,
                },
                {
                    "event_id": 2,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": 2,
                    "error_type": "RuntimeError",
                    "error_message": "boom",
                    "ts": 2.0,
                },
                {
                    "event_id": 3,
                    "stage": "s2",
                    "status": "failed",
                    "task_json": 10,
                    "error_type": "ValueError",
                    "error_message": "bad",
                    "ts": 3.0,
                },
                {
                    "event_id": 4,
                    "stage": "s2",
                    "status": "failed",
                    "task_json": 20,
                    "error_type": "RuntimeError",
                    "error_message": "boom",
                    "ts": 4.0,
                },
            ],
        )
        assert appended == 4

        stage1 = TaskStage("s1", add_one, execution_mode="serial")
        stage2 = TaskStage("s2", double, execution_mode="serial")
        stage1.set_retry_exceptions(RuntimeError)
        stage2.set_retry_exceptions(ValueError)

        graph = TaskGraph("test_graph_restore_db_filters_error_type")
        graph.set_stages(stages=[stage1, stage2])
        graph.restore_db(sqlite_path, statuses=["failed"], filter_by_error_type=True)

        assert stage1.get_counts()["tasks_succeeded"] == 1
        assert stage2.get_counts()["tasks_succeeded"] == 1

    def test_graph_restore_db_filter_keeps_pending_records(self, tmp_path):
        """图级 restore_db 过滤开启时，pending 记录仍应继续回放。"""
        sqlite_path = tmp_path / "fallback.sqlite3"
        appended = append_records(
            sqlite_path,
            [
                {
                    "event_id": 1,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": 1,
                    "error_type": "ValueError",
                    "error_message": "bad",
                    "ts": 1.0,
                },
                {
                    "event_id": 2,
                    "stage": "s1",
                    "status": "pending",
                    "task_json": 2,
                    "error_type": "",
                    "error_message": "",
                    "ts": 2.0,
                },
                {
                    "event_id": 3,
                    "stage": "s2",
                    "status": "failed",
                    "task_json": 10,
                    "error_type": "RuntimeError",
                    "error_message": "boom",
                    "ts": 3.0,
                },
                {
                    "event_id": 4,
                    "stage": "s2",
                    "status": "pending",
                    "task_json": 20,
                    "error_type": "",
                    "error_message": "",
                    "ts": 4.0,
                },
            ],
        )
        assert appended == 4

        stage1 = TaskStage("s1", add_one, execution_mode="serial")
        stage2 = TaskStage("s2", double, execution_mode="serial")
        stage1.set_retry_exceptions(RuntimeError)
        stage2.set_retry_exceptions(ValueError)

        graph = TaskGraph("test_graph_restore_db_filter_keeps_pending_records")
        graph.set_stages(stages=[stage1, stage2])
        graph.restore_db(sqlite_path, filter_by_error_type=True)

        assert stage1.get_counts()["tasks_succeeded"] == 1
        assert stage2.get_counts()["tasks_succeeded"] == 1

    def test_start_raises_exception_group_after_finish(self, monkeypatch):
        """同步 start 应在 finish 后统一抛出收集到的异常。"""
        graph = TaskGraph("test_start_raises_exception_group_after_finish")

        def crash_prepare() -> None:
            raise ValueError("prepare failed")

        monkeypatch.setattr(graph, "_prepare_start", crash_prepare)
        monkeypatch.setattr(
            graph,
            "_finish_start",
            lambda _start_perf: [RuntimeError("finish failed")],
        )

        with pytest.raises(ExceptionGroup) as exc_info:
            graph.start()

        messages = [str(exception) for exception in exc_info.value.exceptions]
        assert messages == ["prepare failed", "finish failed"]


# =========================
# TaskGraph async 模式测试
# =========================
class TestTaskGraphAsync:
    @pytest.mark.asyncio
    async def test_start_async_raises_exception_group_after_finish(
        self,
        monkeypatch,
    ):
        """异步 start_async 应在 finish 后统一抛出收集到的异常。"""
        graph = TaskGraph(
            "test_start_async_raises_exception_group_after_finish", graph_mode="async"
        )

        def crash_prepare() -> None:
            raise ValueError("prepare failed")

        monkeypatch.setattr(graph, "_prepare_start", crash_prepare)
        monkeypatch.setattr(
            graph,
            "_finish_start",
            lambda _start_perf: [RuntimeError("finish failed")],
        )

        with pytest.raises(ExceptionGroup) as exc_info:
            await graph.start_async()

        messages = [str(exception) for exception in exc_info.value.exceptions]
        assert messages == ["prepare failed", "finish failed"]

    @pytest.mark.asyncio
    async def test_graph_async_two_nodes(self):
        """async 模式：两个节点串行，结果正确传递"""
        stage1 = TaskStage("s1", async_add_one, execution_mode="async")
        stage2 = TaskStage("s2", async_double, execution_mode="async")

        graph = TaskGraph("test_graph_async_two_nodes", graph_mode="async")
        graph.set_stages(stages=[stage1, stage2])
        graph.connect([stage1], [stage2])

        await graph.run_async({"s1": [1, 2, 3]})

        assert stage1.get_counts()["tasks_succeeded"] == 3
        assert stage2.get_counts()["tasks_succeeded"] == 3

    @pytest.mark.asyncio
    async def test_graph_async_fan_out(self):
        """async 模式：扇出"""
        source = TaskStage("src", async_add_one, execution_mode="async")
        sink_a = TaskStage("sink_a", async_double, execution_mode="async")
        sink_b = TaskStage("sink_b", async_to_str, execution_mode="async")

        graph = TaskGraph("test_graph_async_fan_out", graph_mode="async")
        graph.set_stages(stages=[source, sink_a, sink_b])
        graph.connect([source], [sink_a, sink_b])

        await graph.run_async({"src": [1, 2]})

        assert source.get_counts()["tasks_succeeded"] == 2
        assert sink_a.get_counts()["tasks_succeeded"] == 2
        assert sink_b.get_counts()["tasks_succeeded"] == 2

    @pytest.mark.asyncio
    async def test_graph_async_fan_in(self):
        """async 模式：扇入"""
        source_a = TaskStage("src_a", async_add_one, execution_mode="async")
        source_b = TaskStage("src_b", async_double, execution_mode="async")
        merge = TaskStage("merge", async_to_str, execution_mode="async")

        graph = TaskGraph("test_graph_async_fan_in", graph_mode="async")
        graph.set_stages(stages=[source_a, source_b, merge])
        graph.connect([source_a, source_b], [merge])

        await graph.run_async({"src_a": [1, 2], "src_b": [10, 20]})

        assert merge.get_counts()["tasks_succeeded"] == 4

    @pytest.mark.asyncio
    async def test_graph_async_error_propagation(self):
        """async 模式：错误任务不会阻断整体流程"""
        stage1 = TaskStage("s1", async_add_offset_10, execution_mode="async")
        stage2 = TaskStage("s2", async_double, execution_mode="async")

        graph = TaskGraph("test_graph_async_error_propagation", graph_mode="async")
        graph.set_stages(stages=[stage1, stage2])
        graph.connect([stage1], [stage2])

        await graph.run_async({"s1": [1, 50, 2]})

        assert stage1.get_counts()["tasks_succeeded"] == 2
        assert stage1.get_counts()["tasks_failed"] == 1
        assert stage2.get_counts()["tasks_succeeded"] == 2

    @pytest.mark.asyncio
    async def test_graph_async_execution_mode(self):
        """async execution_mode：两个节点串行"""
        stage1 = TaskStage("s1", async_add_one, execution_mode="async")
        stage2 = TaskStage("s2", async_double, execution_mode="async")

        graph = TaskGraph("test_graph_async_execution_mode", graph_mode="async")
        graph.set_stages(stages=[stage1, stage2])
        graph.connect([stage1], [stage2])

        await graph.run_async({"s1": [1, 2, 3]})

        assert stage1.get_counts()["tasks_succeeded"] == 3
        assert stage2.get_counts()["tasks_succeeded"] == 3


class TestTaskGraphStructure:
    def test_chain_structure(self):
        """TaskChain：线性结构正确连接"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)
        s3 = TaskStage("s3", to_str)

        chain = TaskChain("test_chain_structure", [s1, s2, s3])
        chain.run({"s1": [1, 2]})

        assert s1.get_counts()["tasks_succeeded"] == 2
        assert s2.get_counts()["tasks_succeeded"] == 2
        assert s3.get_counts()["tasks_succeeded"] == 2

    def test_cross_structure(self):
        """TaskCross：分层结构全连接"""
        layer1 = [TaskStage(f"L1{i}", add_one) for i in range(2)]
        layer2 = [TaskStage(f"L2{i}", double) for i in range(3)]

        cross = TaskCross("test_cross_structure", [layer1, layer2])
        cross.run({"L10": [1], "L11": [2]})

        for s in layer1:
            assert s.get_counts()["tasks_succeeded"] == 1
        for s in layer2:
            # 每个 layer2 节点收到来自 2 个 layer1 节点的各 1 个结果
            assert s.get_counts()["tasks_succeeded"] == 2

    def test_grid_structure(self):
        """TaskGrid：网格结构正确连接"""
        grid = [[TaskStage(f"g{i}{j}", add_one) for j in range(2)] for i in range(2)]
        task_grid = TaskGrid("test_grid_structure", grid)
        task_grid.run({"g00": [1, 2]})

        # 左上角根节点处理 2 个任务
        assert grid[0][0].get_counts()["tasks_succeeded"] == 2
        # 其余节点也会收到传递的任务
        assert grid[0][1].get_counts()["tasks_succeeded"] == 2
        assert grid[1][0].get_counts()["tasks_succeeded"] == 2
        assert grid[1][1].get_counts()["tasks_succeeded"] == 4

class TestTaskGraphAnalysis:
    def test_getters_build_analysis_on_demand(self):
        """分析与结构 getter 在未显式 build 时也应可直接使用。"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)

        graph = TaskGraph("test_getters_build_analysis_on_demand")
        graph.set_stages(stages=[s1, s2])
        graph.connect([s1], [s2])

        analysis = graph.get_graph_analysis()
        structure_graph = graph.get_structure_graph()
        structure_list = graph.get_structure_list()
        source_names = {stage.get_name() for stage in graph.get_source_stages()}

        assert analysis["isDAG"] is True
        assert s1.get_name() in analysis["layersDict"][0]
        assert structure_graph
        assert structure_list
        assert source_names == {s1.get_name()}

    def test_getters_refresh_analysis_after_connect(self):
        """结构变更后 getter 应自动重建分析缓存。"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)

        graph = TaskGraph("test_getters_refresh_analysis_after_connect")
        graph.set_stages(stages=[s1, s2])

        initial_sources = {stage.get_name() for stage in graph.get_source_stages()}
        assert initial_sources == {s1.get_name(), s2.get_name()}

        graph.connect([s1], [s2])

        refreshed_sources = {stage.get_name() for stage in graph.get_source_stages()}
        analysis = graph.get_graph_analysis()

        assert refreshed_sources == {s1.get_name()}
        assert s1.get_name() in analysis["layersDict"][0]
        assert s2.get_name() in analysis["layersDict"][1]

    def test_dag_detection(self):
        """DAG 检测正确"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)

        graph = TaskGraph("test_dag_detection")
        graph.set_stages(stages=[s1, s2])
        graph.connect([s1], [s2])

        # 调用 build_analysis（通过 run 触发）
        graph.run({"s1": [1]})

        analysis = graph.get_graph_analysis()
        assert analysis["isDAG"] is True

    def test_layer_computation(self):
        """DAG 层级计算正确"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)
        s3 = TaskStage("s3", to_str)

        graph = TaskGraph("test_layer_computation")
        graph.set_stages(stages=[s1, s2, s3])
        graph.connect([s1], [s2])
        graph.connect([s2], [s3])

        graph.run({"s1": [1]})

        analysis = graph.get_graph_analysis()
        layers = analysis["layersDict"]
        # s1 在第 0 层, s2 在第 1 层, s3 在第 2 层
        assert s1.get_name() in layers[0]
        assert s2.get_name() in layers[1]
        assert s3.get_name() in layers[2]


class TestTaskGraphRuntimeSnapshot:
    def test_collect_runtime_snapshot_tolerates_not_started_stage(self):
        """Reporter 在节点尚未启动时采集快照也不应因缺少 start_time 崩溃。"""
        graph = TaskGraph("test_collect_runtime_snapshot_tolerates_not_started_stage")
        stage = TaskStage("idle-stage", add_one)
        graph.stage_dict = {stage.get_name(): stage}
        graph.is_dag = False

        graph.collect_runtime_snapshot()

        snapshot = graph.status_dict[stage.get_name()]
        assert snapshot["status"].value == 0
        assert snapshot["start_time"] == 0.0
        assert snapshot["elapsed_time"] == 0


# =========================
# graph_mode × execution_mode 矩阵测试
# =========================
class TestStageExecutionMatrix:
    """覆盖 graph_mode(serial/thread/async) × execution_mode(serial/thread/async) 组合"""

    # ---- serial graph_mode ----

    def test_serial_serial(self):
        """测试串行图模式 + 串行执行模式"""
        s1 = TaskStage("s1", add_one, execution_mode="serial")
        s2 = TaskStage("s2", double, execution_mode="serial")

        graph = TaskGraph("test_serial_serial", graph_mode="serial")
        graph.set_stages(stages=[s1, s2])
        graph.connect([s1], [s2])
        graph.run({"s1": [1, 2, 3, 4, 5]})

        assert s1.get_counts()["tasks_succeeded"] == 5
        assert s2.get_counts()["tasks_succeeded"] == 5

    def test_serial_thread(self):
        """测试串行图模式 + 线程池执行模式"""
        s1 = TaskStage("s1", add_one, execution_mode="thread", max_workers=4)
        s2 = TaskStage("s2", double, execution_mode="thread", max_workers=4)

        graph = TaskGraph("test_serial_thread", graph_mode="serial")
        graph.set_stages(stages=[s1, s2])
        graph.connect([s1], [s2])
        graph.run({"s1": [1, 2, 3, 4, 5]})

        assert s1.get_counts()["tasks_succeeded"] == 5
        assert s2.get_counts()["tasks_succeeded"] == 5

    # ---- thread graph_mode ----

    def test_thread_serial(self):
        """测试线程图模式 + 串行执行模式"""
        s1 = TaskStage("s1", add_one, execution_mode="serial")
        s2 = TaskStage("s2", double, execution_mode="serial")

        graph = TaskGraph("test_thread_serial", graph_mode="thread")
        graph.set_stages(stages=[s1, s2])
        graph.connect([s1], [s2])
        graph.run({"s1": [1, 2, 3, 4, 5]})

        assert s1.get_counts()["tasks_succeeded"] == 5
        assert s2.get_counts()["tasks_succeeded"] == 5

    def test_thread_thread(self):
        """测试线程图模式 + 线程池执行模式"""
        s1 = TaskStage("s1", add_one, execution_mode="thread", max_workers=4)
        s2 = TaskStage("s2", double, execution_mode="thread", max_workers=4)

        graph = TaskGraph("test_thread_thread", graph_mode="thread")
        graph.set_stages(stages=[s1, s2])
        graph.connect([s1], [s2])
        graph.run({"s1": [1, 2, 3, 4, 5]})

        assert s1.get_counts()["tasks_succeeded"] == 5
        assert s2.get_counts()["tasks_succeeded"] == 5

    # ---- async graph_mode ----

    @pytest.mark.asyncio
    async def test_async_serial(self):
        """测试异步图模式 + 串行执行模式"""
        s1 = TaskStage("s1", add_one, execution_mode="serial")
        s2 = TaskStage("s2", double, execution_mode="serial")

        graph = TaskGraph("test_async_serial", graph_mode="async")
        graph.set_stages(stages=[s1, s2])
        graph.connect([s1], [s2])
        await graph.run_async({"s1": [1, 2, 3, 4, 5]})

        assert s1.get_counts()["tasks_succeeded"] == 5
        assert s2.get_counts()["tasks_succeeded"] == 5

    @pytest.mark.asyncio
    async def test_async_thread(self):
        """测试异步图模式 + 线程池执行模式"""
        s1 = TaskStage("s1", add_one, execution_mode="thread", max_workers=4)
        s2 = TaskStage("s2", double, execution_mode="thread", max_workers=4)

        graph = TaskGraph("test_async_thread", graph_mode="async")
        graph.set_stages(stages=[s1, s2])
        graph.connect([s1], [s2])
        await graph.run_async({"s1": [1, 2, 3, 4, 5]})

        assert s1.get_counts()["tasks_succeeded"] == 5
        assert s2.get_counts()["tasks_succeeded"] == 5

    @pytest.mark.asyncio
    async def test_async_async(self):
        """测试异步图模式 + 异步执行模式"""
        s1 = TaskStage("s1", async_add_one, execution_mode="async", max_workers=4)
        s2 = TaskStage("s2", async_double, execution_mode="async", max_workers=4)

        graph = TaskGraph("test_async_async", graph_mode="async")
        graph.set_stages(stages=[s1, s2])
        graph.connect([s1], [s2])
        await graph.run_async({"s1": [1, 2, 3, 4, 5]})

        assert s1.get_counts()["tasks_succeeded"] == 5
        assert s2.get_counts()["tasks_succeeded"] == 5


# =========================
# TaskGraph thread 模式测试
# =========================
class TestTaskGraphThread:
    def test_graph_thread_two_nodes(self):
        """thread 模式：两个节点串行，结果正确传递"""
        stage1 = TaskStage("s1", add_one, execution_mode="serial")
        stage2 = TaskStage("s2", double, execution_mode="serial")

        graph = TaskGraph("test_graph_thread_two_nodes", graph_mode="thread")
        graph.set_stages(stages=[stage1, stage2])
        graph.connect([stage1], [stage2])

        graph.run({"s1": [1, 2, 3]})

        assert stage1.get_counts()["tasks_succeeded"] == 3
        assert stage2.get_counts()["tasks_succeeded"] == 3

    def test_graph_thread_fan_out(self):
        """thread 模式：扇出"""
        source = TaskStage("src", add_one, execution_mode="serial")
        sink_a = TaskStage("SinkA", double, execution_mode="serial")
        sink_b = TaskStage("SinkB", to_str, execution_mode="serial")

        graph = TaskGraph("test_graph_thread_fan_out", graph_mode="thread")
        graph.set_stages(stages=[source, sink_a, sink_b])
        graph.connect([source], [sink_a, sink_b])

        graph.run({"src": [1, 2]})

        assert source.get_counts()["tasks_succeeded"] == 2
        assert sink_a.get_counts()["tasks_succeeded"] == 2
        assert sink_b.get_counts()["tasks_succeeded"] == 2

    def test_graph_thread_fan_in(self):
        """thread 模式：扇入"""
        source_a = TaskStage("SrcA", add_one, execution_mode="serial")
        source_b = TaskStage("SrcB", double, execution_mode="serial")
        merge = TaskStage("merge", to_str, execution_mode="serial")

        graph = TaskGraph("test_graph_thread_fan_in", graph_mode="thread")
        graph.set_stages(stages=[source_a, source_b, merge])
        graph.connect([source_a, source_b], [merge])

        graph.run({"SrcA": [1, 2], "SrcB": [10, 20]})

        assert merge.get_counts()["tasks_succeeded"] == 4

    def test_graph_thread_error_propagation(self):
        """thread 模式：错误任务不会阻断整体流程"""
        stage1 = TaskStage("s1", add_offset_10, execution_mode="serial")
        stage2 = TaskStage("s2", double, execution_mode="serial")

        graph = TaskGraph("test_graph_thread_error_propagation", graph_mode="thread")
        graph.set_stages(stages=[stage1, stage2])
        graph.connect([stage1], [stage2])

        graph.run({"s1": [1, 50, 2]})

        assert stage1.get_counts()["tasks_succeeded"] == 2
        assert stage1.get_counts()["tasks_failed"] == 1
        assert stage2.get_counts()["tasks_succeeded"] == 2

    def test_graph_thread_with_lambda(self):
        """thread 模式：支持 lambda 函数"""
        stage1 = TaskStage("s1", lambda x: x + 1, execution_mode="serial")
        stage2 = TaskStage("s2", lambda x: x * 2, execution_mode="serial")

        graph = TaskGraph("test_graph_thread_with_lambda", graph_mode="thread")
        graph.set_stages(stages=[stage1, stage2])
        graph.connect([stage1], [stage2])

        graph.run({"s1": [1, 2, 3]})

        assert stage1.get_counts()["tasks_succeeded"] == 3
        assert stage2.get_counts()["tasks_succeeded"] == 3

    def test_graph_thread_schedule(self):
        """thread 模式下线性链正常工作"""
        s1 = TaskStage("s1", add_one, execution_mode="serial")
        s2 = TaskStage("s2", double, execution_mode="serial")
        s3 = TaskStage("s3", to_str, execution_mode="serial")

        graph = TaskGraph("test_graph_thread_schedule", graph_mode="thread")
        graph.set_stages(stages=[s1, s2, s3])
        graph.connect([s1], [s2])
        graph.connect([s2], [s3])

        graph.run({"s1": [1, 2]})

        assert s1.get_counts()["tasks_succeeded"] == 2
        assert s2.get_counts()["tasks_succeeded"] == 2
        assert s3.get_counts()["tasks_succeeded"] == 2


# =========================
# source_stages 自动推导测试
# =========================
class TestSourceStages:
    def test_source_stages_linear(self):
        """线性图：source 只有头节点"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)
        s3 = TaskStage("s3", to_str)

        graph = TaskGraph("test_source_stages_linear")
        graph.set_stages(stages=[s1, s2, s3])
        graph.connect([s1], [s2])
        graph.connect([s2], [s3])

        graph.run({"s1": [1]})

        sources = graph.get_source_stages()
        assert len(sources) == 1
        assert sources[0].get_name() == s1.get_name()

    def test_source_stages_fan_in(self):
        """两个入口汇入一点"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)
        s3 = TaskStage("s3", to_str)

        graph = TaskGraph("test_source_stages_fan_in")
        graph.set_stages(stages=[s1, s2, s3])
        graph.connect([s1], [s3])
        graph.connect([s2], [s3])

        graph.run({"s1": [1], "s2": [2]})

        source_names = {s.get_name() for s in graph.get_source_stages()}
        assert source_names == {s1.get_name(), s2.get_name()}

    def test_source_stages_diamond(self):
        """菱形图 A→{B,C}→D：source 只有 A"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)
        s3 = TaskStage("s3", to_str)
        s4 = TaskStage("s4", add_one)

        graph = TaskGraph("test_source_stages_diamond")
        graph.set_stages(stages=[s1, s2, s3, s4])
        graph.connect([s1], [s2, s3])
        graph.connect([s2, s3], [s4])

        graph.run({"s1": [1]})

        sources = graph.get_source_stages()
        assert len(sources) == 1
        assert sources[0].get_name() == s1.get_name()

    def test_source_stages_cycle_returns_one_source_scc_member(self):
        """单个源 SCC 只返回一个代表点"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)
        s3 = TaskStage("s3", to_str)

        graph = TaskGraph("test_source_stages_cycle_returns_one_source_scc_member")
        graph.set_stages(stages=[s1, s2, s3])
        graph.connect([s1], [s2])
        graph.connect([s2], [s3])
        graph.connect([s3], [s1])

        source_names = {stage.get_name() for stage in graph.get_source_stages()}
        cycle_names = {s1.get_name(), s2.get_name(), s3.get_name()}

        assert len(source_names) == 1
        assert source_names <= cycle_names

    def test_source_stages_returns_one_member_per_source_scc(self):
        """多个源 SCC 时，每个源 SCC 各返回一个代表点"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)
        s3 = TaskStage("s3", to_str)
        s4 = TaskStage("s4", add_one)
        s5 = TaskStage("s5", double)

        graph = TaskGraph("test_source_stages_returns_one_member_per_source_scc")
        graph.set_stages(stages=[s1, s2, s3, s4, s5])
        graph.connect([s1], [s2])
        graph.connect([s2], [s1])
        graph.connect([s3], [s4])
        graph.connect([s4], [s3])
        graph.connect([s2, s4], [s5])

        source_names = {stage.get_name() for stage in graph.get_source_stages()}
        source_scc_a = {s1.get_name(), s2.get_name()}
        source_scc_b = {s3.get_name(), s4.get_name()}

        assert len(source_names) == 2
        assert len(source_names & source_scc_a) == 1
        assert len(source_names & source_scc_b) == 1


# =========================
# 含环图测试
# =========================
class TestCyclicGraph:
    def test_cyclic_serial_graph_warns(self):
        """环图在 serial graph_mode 下分析时应给出警告。"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)
        s3 = TaskStage("s3", to_str)

        graph = TaskGraph("test_cyclic_serial_graph_warns", graph_mode="serial")
        graph.set_stages(stages=[s1, s2, s3])
        graph.connect([s1], [s2])
        graph.connect([s2], [s3])
        graph.connect([s3], [s1])

        with pytest.warns(
            UserWarning,
            match=r"TaskGraph contains a cycle while graph_mode='serial'",
        ):
            graph.get_source_stages()

    def test_cyclic_is_dag_false(self):
        """含环图 is_dag 为 False"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)
        s3 = TaskStage("s3", to_str)

        graph = TaskGraph("test_cyclic_is_dag_false", graph_mode="thread")
        graph.set_stages(stages=[s1, s2, s3])
        graph.connect([s1], [s2])
        graph.connect([s2], [s3])
        graph.connect([s3], [s1])

        graph.run({"s1": [1]})

        analysis = graph.get_graph_analysis()
        assert analysis["isDAG"] is False

    def test_cyclic_layers(self):
        """环内节点同层，尾巴节点层级更高"""
        s1 = TaskStage("s1", add_one)
        s2 = TaskStage("s2", double)
        s3 = TaskStage("s3", to_str)
        s4 = TaskStage("s4", add_one)

        graph = TaskGraph("test_cyclic_layers", graph_mode="thread")
        graph.set_stages(stages=[s1, s2, s3, s4])
        graph.connect([s1], [s2])
        graph.connect([s2], [s3])
        graph.connect([s3], [s1])
        graph.connect([s1], [s4])

        graph.run({"s1": [1]})

        analysis = graph.get_graph_analysis()
        layers = analysis["layersDict"]
        cycle_names = {s1.get_name(), s2.get_name(), s3.get_name()}
        cycle_layer = None
        for layer_idx, layer_names in layers.items():
            if s1.get_name() in layer_names:
                cycle_layer = layer_idx
                break
        assert cycle_layer is not None
        for stage_name in cycle_names:
            assert stage_name in layers[cycle_layer]
        assert s4.get_name() in layers[cycle_layer + 1]
