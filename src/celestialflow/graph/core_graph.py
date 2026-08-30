# graph/core_graph.py
from __future__ import annotations

import asyncio
import threading
import time
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..observability import NullTaskReporter, ReporterProtocol
from ..persistence import funnel_scope, get_lifecycle_spout, get_log_inlet
from ..persistence.util_sqlite import load_tasks_grouped_by_stage
from ..runtime.util_errors import (
    ConfigurationError,
    DuplicateNodeError,
    InvalidOptionError,
    NodeNotFoundError,
)
from ..runtime.util_estimators import calc_remaining
from ..runtime.util_event import EventClient, LocalEventClient
from ..runtime.util_format import cluster_by_value_sorted
from ..stage.core_stage import TaskStage
from ..stage.util_types import AnyTaskStage
from .util_estimators import calc_global_pending
from .util_order_graph import OrderGraph, compute_node_levels, is_dag, source_nodes
from .util_render import render_structure_list


class TaskGraph:
    """任务图核心类，负责构建、连接和调度一组 TaskStage 节点。

    注意：
    - TaskGraph 是一次性对象，设计上只应启动一次。
    - start() / start_async() 执行后，内部会建立并持有运行期资源、队列绑定和线程状态，
      不保证可被安全重置或重复启动。
    - 如需再次运行相同流程，请重新创建 TaskGraph 实例及其关联的 TaskStage。
    """

    # ==== 类级类型注解 ====
    name: str
    graph_id: str
    graph_mode: str
    threads: list[threading.Thread]
    stage_dict: dict[str, AnyTaskStage]
    status_dict: dict[str, dict[str, Any]]
    status_timestamp: float
    _analysis_dirty: bool
    source_names: list[str]
    order_graph: OrderGraph
    start_time: float
    reporter: ReporterProtocol
    ctree_client: EventClient
    is_dag: bool
    layers_dict: dict[int, list[str]]

    # ==== 初始化 ====

    def __init__(
        self,
        name: str,
        graph_mode: str = "serial",
    ) -> None:
        """
        初始化 TaskGraph 实例。

        TaskGraph 表示一组 TaskStage 节点所构成的任务图，可用于构建并行、串行、
        分层等多种形式的任务执行流程。所有节点一次性调度并发执行，依赖关系通过
        队列流自动控制。

        生命周期说明：
        - 当前 TaskGraph 实例为一次性对象。
        - 完成一次 start() / start_async() 后，不应复用同一实例再次启动。
        - 如需重复执行，请重新构建新的 TaskGraph 与节点对象。

        :param name: 任务图名称
        :param graph_mode: 图执行模式, 可选值为 'serial'（串行）、'thread'（线程）或 'async'（异步），默认 'serial'
        """
        self._set_name(name)
        self.set_graph_mode(graph_mode)
        self.set_reporter(NullTaskReporter())
        self.set_ctree(LocalEventClient())

        self._init_state()

    def _init_state(self) -> None:
        """
        初始化任务图运行时状态。
        """
        # 用于保存所有子线程的引用
        self.threads = []

        # 用于保存每个节点的运行信息
        self.stage_dict = {}

        # 用于保存每个节点的上一次collect_runtime_snapshot()的状态信息
        self.status_dict = defaultdict(dict)

        # 用于保存最近一次状态快照对应的统一时间戳
        self.status_timestamp = 0.0

        # 用于保存源节点列表（由 _build_analysis 自动计算）
        self.source_names = []

        # 用于保存图结构的邻接表
        self.order_graph = OrderGraph()
        self._analysis_dirty = True

        # 用于保存任务图启动时间
        self.start_time = 0.0

    # ==== 建图 ====

    def set_stages(self, stages: list[AnyTaskStage]) -> None:
        """
        添加节点到任务图中

        :param stages: 待添加的节点列表
        :raises DuplicateNodeError: 存在重复的 stage 名称
        """
        for stage in stages:
            stage_name = stage.get_name()
            if stage_name in self.stage_dict:
                raise DuplicateNodeError(f"duplicate stage name: {stage_name}")
            self.stage_dict[stage_name] = stage
            self.order_graph.add_node(stage_name)

            stage.set_ctree(self.ctree_client)

        self._analysis_dirty = True

    def connect[R](
        self,
        from_stages: list[TaskStage[Any, R]],
        to_stages: list[TaskStage[R, Any]],
    ) -> None:
        """
        建立超边连接：from_stages 中的每个节点连接到 to_stages 中的每个节点。

        :param from_stages: 上游节点列表
        :param to_stages: 下游节点列表
        """
        for from_stage in from_stages:
            from_name = from_stage.get_name()
            from_out_queue = from_stage.result_queue

            if from_name not in self.stage_dict:
                raise NodeNotFoundError(f"from stage not found: {from_name}")

            for to_stage in to_stages:
                to_name = to_stage.get_name()
                to_in_queue = to_stage.task_queue

                if to_name not in self.stage_dict:
                    raise NodeNotFoundError(f"to stage not found: {to_name}")

                to_stage.prev_binding(from_stage)
                from_out_queue.add_queue(to_in_queue, to_name)
                to_in_queue.add_source_name(from_name)
                self.order_graph.add_edge(from_name, to_name)

        self._analysis_dirty = True

    # ==== 配置 ====

    def _set_name(self, name: str) -> None:
        """
        设置任务图名称

        :param name: 任务图名称
        """
        self.name = name
        self.graph_id = f"{name}@{int(time.time() * 1000)}"

    def set_graph_mode(self, graph_mode: str) -> None:
        """
        设置图执行模式。

        :param graph_mode: 图执行模式, 可选值为 'serial'（串行）或 'thread'（线程）或 'async'（异步）
        :raises InvalidOptionError: graph_mode 不是 'serial' 或 'thread' 或 'async'
        """
        valid_modes = ("serial", "thread", "async")
        if graph_mode not in valid_modes:
            raise InvalidOptionError("graph mode", graph_mode, valid_modes)
        self.graph_mode = graph_mode

    def set_stage_execution_mode(self, execution_mode: str) -> None:
        """
        设置任务链的执行模式

        :param execution_mode: 节点内部执行模式, 可选值为 'serial', 'thread' 或 'async'
        """
        for stage in self.stage_dict.values():
            stage.set_execution_mode(execution_mode)
        self._build_analysis()

    def set_reporter(self, reporter: ReporterProtocol) -> None:
        """
        设定任务图绑定的 reporter。

        :param reporter: 需绑定到当前任务图的 reporter 实例
        """
        self.reporter = reporter

    def set_ctree(self, ctree_client: EventClient) -> None:
        """
        设置任务图共享的事件客户端。

        :param ctree_client: 事件客户端实例
        """
        self.ctree_client = ctree_client
        if not hasattr(self, "stage_dict"):
            return
        for stage in self.stage_dict.values():
            stage.set_ctree(ctree_client)

    # ==== 分析图 ====

    def _ensure_analysis(self) -> None:
        """按需重建图分析缓存。"""
        if self._analysis_dirty:
            self._build_analysis()

    def _build_analysis(self) -> None:
        """
        分析任务图，计算源节点、是否为 DAG 与层级信息。

        :raises ConfigurationError: serial 模式下图含环（非 DAG）时触发
        :return: ``None``。
        """
        self.source_names = source_nodes(self.order_graph)
        self.is_dag = is_dag(self.order_graph)

        stage_level_dict = compute_node_levels(self.order_graph)
        self.layers_dict = cluster_by_value_sorted(stage_level_dict)
        self._analysis_dirty = False

        if not self.is_dag and self.graph_mode == "serial":
            raise ConfigurationError(
                "TaskGraph contains a cycle while graph_mode='serial'; "
                "serial startup may block or leave tasks unconsumed. "
                "Consider using graph_mode='thread' or 'async'."
            )

    def put_source_signal(self) -> None:
        """
        将终止信号放入所有源节点的队列中。
        """
        for source_name in self.source_names:
            self.stage_dict[source_name].put_signal()

    # ==== 执行 ====

    def run(
        self,
        init_tasks_dict: dict[str, Iterable[Any]],
        *,
        if_put_signal: bool = True,
    ) -> None:
        """
        运行任务链，注入初始任务并启动执行。

        :param init_tasks_dict: 任务列表字典，键为 stage 名称，值为任务列表
        :param if_put_signal: 是否注入终止信号，默认 True
        :return: ``None``
        """
        self._build_analysis()
        with funnel_scope():
            for stage_name, tasks in init_tasks_dict.items():
                for task in tasks:
                    self.stage_dict[stage_name].put_task(task)
            if if_put_signal:
                self.put_source_signal()
            self.start()

    async def run_async(
        self,
        init_tasks_dict: dict[str, Iterable[Any]],
        *,
        if_put_signal: bool = True,
    ) -> None:
        """
        运行任务链，注入初始任务并启动执行。

        :param init_tasks_dict: 初始任务字典，键为 stage 名称，值为任务可迭代对象
        :param if_put_signal: 是否注入终止信号，默认 True
        :return: ``None``
        """
        self._build_analysis()
        with funnel_scope():
            for stage_name, tasks in init_tasks_dict.items():
                for task in tasks:
                    self.stage_dict[stage_name].put_task(task)
            if if_put_signal:
                self.put_source_signal()
            await self.start_async()

    def restore_db(
        self,
        db_path: str | Path,
        statuses: Iterable[str] | None = None,
        *,
        filter_by_error_type: bool = False,
        if_put_signal: bool = True,
    ) -> None:
        """
        从 sqlite 持久化库中读取任务，按 stage 分组后启动任务图。

        :param db_path: sqlite 数据库文件路径
        :param statuses: 记录状态过滤列表，默认 ``["failed", "pending"]``
        :param filter_by_error_type: 是否按各 stage 的 ``retry_exceptions`` 过滤
            ``error_type``，默认 ``False``
        :param if_put_signal: 是否在恢复任务注入后，为所有源节点补发终止信号，
            默认 ``True``
        """
        statuses = ["failed", "pending"] if statuses is None else statuses
        grouped_records = load_tasks_grouped_by_stage(db_path, statuses)
        tasks: dict[str, Iterable[Any]] = {}

        for name, records in grouped_records.items():
            stage = self.stage_dict[name]
            if filter_by_error_type and name in self.stage_dict:
                retry_error_type_names = stage.metrics.get_retry_error_type_names()
                records = [
                    record
                    for record in records
                    if str(record["error_type"]) in retry_error_type_names
                    or record["status"] == "pending"
                ]
            tasks[name] = [record["task_json"] for record in records]

        self.run(tasks, if_put_signal=if_put_signal)

    # ==== 启动 ====

    def _prepare_start(
        self,
    ) -> None:
        """
        启动前准备：图分析、必要警告与运行时资源启动。

        本方法会创建线程与文件句柄等运行时资源，调用方应保证在 finally 中
        执行 :meth:`_finish_start` 完成收尾。

        :return: ``None``
        """
        get_log_inlet().start_graph(self.name, self.get_structure_list())
        self.reporter.start()

    def _finish_start(self, start_perf: float) -> list[Exception]:
        """
        启动后收尾：回收图内状态、停止上报器并记录结束日志。

        ``lifecycle`` / ``log`` spout 的启停由外层 ``funnel_scope()`` 统一管理，
        本方法只负责图对象自身的收尾逻辑。

        :param start_perf: 启动时刻的 ``perf_counter`` 时间戳，用于计算运行耗时
        :return: 收集到的收尾阶段异常列表
        """
        error_list: list[Exception] = []

        try:
            # 收集并持久化每个节点中未消费的任务
            for stage in self.stage_dict.values():
                stage.drain_task_queue()
        except Exception as exception:
            error_list.append(exception)

        try:
            self.collect_runtime_snapshot()
        except Exception as exception:
            error_list.append(exception)

        try:
            self.reporter.stop()
        except Exception as exception:
            error_list.append(exception)

        try:
            get_log_inlet().end_graph(self.name, time.perf_counter() - start_perf)
        except Exception as exception:
            error_list.append(exception)

        self.threads.clear()  # 清理已 join 的线程引用

        return error_list

    def start(self) -> None:
        """
        启动任务链。

        根据 :attr:`graph_mode` 选择串行或线程方式启动所有节点。

        提示：
        - 本方法为同步启动入口。
        - 若当前线程已运行事件循环，且图中包含 ``execution_mode='async'`` 的节点，
          可能触发 ``asyncio.run`` 的嵌套限制；此时更适合使用 :meth:`start_async`
          或 :meth:`run_async`。

        :note:
            TaskGraph 为一次性对象；当前实例启动并运行完成后，不保证可安全再次调用
            start()。如需重复执行，请创建新的 TaskGraph 实例。
        """
        start_perf = time.perf_counter()
        self.start_time = time.time()
        error_list: list[Exception] = []

        try:
            self._prepare_start()

            if self.graph_mode == "serial":
                self._execute_stages_serial()
            elif self.graph_mode == "thread":
                self._execute_stages_thread()
            else:
                raise InvalidOptionError(
                    "graph mode", self.graph_mode, ("serial", "thread")
                )
        except Exception as exception:
            error_list.append(exception)
        finally:
            error_list.extend(self._finish_start(start_perf))

        if error_list:
            raise ExceptionGroup("Errors occurred during graph execution", error_list)

    async def start_async(self) -> None:
        """
        以异步方式启动任务图，适合在已运行事件循环的上下文中调用。

        与同步 :meth:`start` 的区别：
        - async 执行模式的节点通过 :meth:`TaskStage.start_async` 以协程方式运行，
          不再内部调用 ``asyncio.run``，避免嵌套事件循环导致的崩溃。
        - serial / thread 执行模式的节点通过 ``asyncio.to_thread`` 在独立线程中运行，
          避免阻塞事件循环。
        :note:
            TaskGraph 为一次性对象；当前实例启动并运行完成后，不保证可安全再次调用
            start_async()。如需重复执行，请创建新的 TaskGraph 实例。
        """
        if self.graph_mode != "async":
            raise InvalidOptionError("graph mode", self.graph_mode, ("async",))

        start_perf = time.perf_counter()
        self.start_time = time.time()
        error_list: list[Exception] = []

        try:
            self._prepare_start()
            await self._execute_stages_async()
        except Exception as exception:
            error_list.append(exception)
        finally:
            error_list.extend(self._finish_start(start_perf))

        if error_list:
            raise ExceptionGroup("Errors occurred during graph execution", error_list)

    def _execute_stages_serial(self) -> None:
        """
        以串行方式按层展开的拓扑序执行所有节点。

        层间按层级升序、层内按注册顺序逐个执行，每个节点执行完毕后才
        启动下一个。层展开序保证每个节点的所有上游都先于它启动，因此
        执行顺序不再依赖节点注册顺序。

        注：图分析（:attr:`layers_dict`）由 :meth:`_prepare_start` 经
        :meth:`get_structure_list` 保证已构建。
        """
        for stage_name_list in self.layers_dict.values():
            for stage_name in stage_name_list:
                stage = self.stage_dict[stage_name]
                self._execute_stage(stage)

    def _execute_stages_thread(self) -> None:
        """
        以线程方式并发执行所有节点。

        每个节点在独立线程中启动，最后统一等待所有线程结束。
        """
        for stage in self.stage_dict.values():
            t = threading.Thread(
                target=self._execute_stage,
                args=(stage,),
                name=stage.get_name(),
                daemon=True,
            )
            t.start()
            self.threads.append(t)

        for t in self.threads:
            t.join()

    async def _execute_stages_async(self) -> None:
        """
        异步执行所有节点：全图并发执行。
        """
        tasks = [
            asyncio.create_task(self._execute_stage_async(stage))
            for stage in self.stage_dict.values()
        ]
        await asyncio.gather(*tasks)

    def _execute_stage(self, stage: AnyTaskStage) -> None:
        """
        在同步图启动路径下执行单个节点。

        :param stage: 节点
        """
        if stage.execution_mode == "async":
            asyncio.run(stage.start_async())
        else:
            stage.start()

    async def _execute_stage_async(self, stage: AnyTaskStage) -> None:
        """
        异步执行单个节点：async 模式走协程，其余模式走线程池。

        :param stage: 节点
        """
        if stage.execution_mode == "async":
            await stage.start_async()
        else:
            await asyncio.to_thread(stage.start)

    # ==== 运行时监控 ====

    def _calc_graph_pending(
        self,
        running_processed_map: dict[str, int],
        running_pending_map: dict[str, int],
    ) -> dict[str, int]:
        """
        根据 DAG/非 DAG 策略计算全局预计待处理任务数量。

        :param running_processed_map: 各节点已处理任务数
        :param running_pending_map: 各节点待处理任务数
        :return: 全局预计待处理任务数量
        """
        if not self.is_dag:
            return running_pending_map

        total_pending_map = calc_global_pending(
            self.order_graph,
            running_processed_map,
            running_pending_map,
        )
        return total_pending_map

    def collect_runtime_snapshot(self) -> None:
        """
        收集运行时快照。

        遍历所有 stage 采集各节点快照，然后计算 DAG 感知的全局 pending 估算值，
        并补充到每个节点的快照中。
        """
        status_dict: dict[str, dict[str, Any]] = {}
        now = time.time()
        interval = self.reporter.interval

        # 为全局预计待处理任务数收集数据
        running_processed_map: dict[str, int] = {}
        running_pending_map: dict[str, int] = {}

        for stage_name, stage in self.stage_dict.items():
            snapshot = stage.snapshot(interval)
            status_dict[stage_name] = snapshot

            running_processed_map[stage_name] = int(snapshot["tasks_processed"] or 0)
            running_pending_map[stage_name] = int(snapshot["tasks_pending"] or 0)

        total_pending_map = self._calc_graph_pending(
            running_processed_map,
            running_pending_map,
        )
        for stage_name, stage_status in status_dict.items():
            stage_status["total_tasks_pending"] = total_pending_map[stage_name]
            stage_status["total_remaining_time"] = calc_remaining(
                stage_status["tasks_processed"],
                stage_status["total_tasks_pending"],
                stage_status["elapsed_time"],
            )

        self.status_dict = status_dict
        self.status_timestamp = now

    # ==== 查询接口 ====

    def get_graph_id(self) -> str:
        """
        获取当前任务图实例的唯一标识。

        :return: graph_id
        """
        return self.graph_id

    def get_stages_summary(self) -> dict[str, dict[str, Any]]:
        """
        获取所有任务阶段的摘要信息

        :return: 任务阶段摘要信息字典
        """
        nodes: dict[str, dict[str, Any]] = {}

        for stage_name, stage in self.stage_dict.items():
            nodes[stage_name] = dict(stage.get_summary())
        return nodes

    def get_edges(self) -> dict[str, list[str]]:
        """
        获取任务图的边邻接表。

        :return: 边信息邻接表 ``{stage_name: [next_stage_name, ...]}``；
            与底层图结构共享引用，调用方应只读
        """
        return self.order_graph.out_edges

    def get_source_names(self) -> list[str]:
        """
        获取源节点列表

        :return: 源节点列表
        """
        self._ensure_analysis()
        return self.source_names

    def get_status_snapshot(self) -> dict[str, Any]:
        """
        获取带统一时间戳的状态快照

        :return: {"timestamp": float, "status": {...}}
        """
        return {
            "timestamp": self.status_timestamp,
            "status": self.status_dict,
        }

    def get_graph_analysis(self) -> dict[str, Any]:
        """
        获取任务图的分析信息

        :return: 包含 ``graphId``、``graphMode``、``name``、``startTime``、
            ``className``、``isDAG`` 与 ``layersDict`` 的字典
        """
        self._ensure_analysis()
        return {
            "graphId": self.graph_id,
            "graphMode": self.graph_mode,
            "name": self.name,
            "startTime": self.start_time,
            "className": self.__class__.__name__,
            "isDAG": self.is_dag,
            "layersDict": self.layers_dict,
        }

    def get_structure_list(self) -> list[str]:
        """
        获取任务图的格式化结构列表

        :return: 带边框的格式化字符串列表
        """
        self._ensure_analysis()
        return render_structure_list(
            self.get_stages_summary(),
            self.order_graph.out_edges,
            self.source_names,
        )

    def get_order_graph(self) -> OrderGraph:
        """
        获取任务图对应的有序有向图视图。

        :return: :class:`OrderGraph` 实例
        """
        return self.order_graph

    def get_lifecycle_path(self) -> Path:
        """
        获取任务生命周期持久化 sqlite 文件路径。

        :return: 生命周期持久化文件的绝对路径，未设置时返回空 Path
        """
        db_path = get_lifecycle_spout().db_path
        if db_path is None:
            return Path()
        return Path(db_path).resolve()
