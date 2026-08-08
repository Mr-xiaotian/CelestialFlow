# graph/core_graph.py
from __future__ import annotations

import asyncio
import threading
import time
import warnings
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..observability import NullTaskReporter, ReporterProtocol
from ..persistence import get_fallback_spout, get_log_inlet, get_log_spout
from ..persistence.util_sqlite import load_tasks_grouped_by_stage
from ..runtime.util_errors import (
    DuplicateNodeError,
    NodeNotFoundError,
    ScheduleModeError,
    StageModeError,
)
from ..runtime.util_estimators import calc_remaining
from ..runtime.util_event import EventClient, LocalEventClient
from ..runtime.util_types import TerminationSignal
from ..stage.core_stage import TaskStage
from ..stage.util_types import AnyTaskStage
from ..utils.util_collections import cluster_by_value_sorted
from .util_estimators import calc_global_pending
from .util_graph import OrderGraph, compute_node_levels, is_dag, source_nodes
from .util_serialize import build_structure_graph, format_structure_list_from_graph


class TaskGraph:
    """任务图核心类，负责构建、连接和调度一组 TaskStage 节点。

    注意：
    - TaskGraph 是一次性对象，设计上只应启动一次。
    - start_graph() 执行后，内部会建立并持有运行期资源、队列绑定和线程状态，
      不保证可被安全重置或重复启动。
    - 如需再次运行相同流程，请重新创建 TaskGraph 实例及其关联的 TaskStage。
    """

    # ==== 类级类型注解 ====
    name: str
    graph_id: str
    schedule_mode: str
    threads: list[threading.Thread]
    stage_dict: dict[str, AnyTaskStage]
    status_dict: dict[str, dict[str, Any]]
    status_timestamp: float
    input_ids: dict[str, set[int]]
    source_stages: list[AnyTaskStage]
    _analysis_dirty: bool
    out_edges: dict[str, list[str]]
    in_edges: dict[str, list[str]]
    order_graph: OrderGraph
    start_time: float
    reporter: ReporterProtocol
    ctree_client: EventClient
    structure_graph: dict[str, Any]
    is_dag: bool
    layers_dict: dict[int, list[str]]

    # ==== 初始化 ====

    def __init__(
        self,
        name: str,
        schedule_mode: str = "eager",
    ) -> None:
        """
        初始化 TaskGraph 实例。

        TaskGraph 表示一组 TaskStage 节点所构成的任务图，可用于构建并行、串行、
        分层等多种形式的任务执行流程。通过分析图结构和调度布局策略，实现灵活的
        DAG 任务调度控制。

        生命周期说明：
        - 当前 TaskGraph 实例为一次性对象。
        - 完成一次 start_graph() 后，不应复用同一实例再次启动。
        - 如需重复执行，请重新构建新的 TaskGraph 与节点对象。

        :param name: 任务图名称
        :param schedule_mode: str, optional, default = 'eager'
            控制任务图的调度布局模式，支持以下两种策略：
            - 'eager'：
                默认模式。所有节点一次性调度并发执行，依赖关系通过队列流自动控制。
                适用于最大化并行度的执行场景。
            - 'staged'：
                分层执行模式。任务图必须为有向无环图（DAG）。
                节点按层级顺序逐层启动，确保上层所有任务完成后再启动下一层。
                更利于调试、性能分析和阶段性资源控制。
        """
        self._set_name(name)
        self._set_schedule_mode(schedule_mode)
        self.set_reporter(NullTaskReporter())
        self.set_ctree(LocalEventClient())

        self._init_state()

    def _init_state(self) -> None:
        """
        初始化任务图运行时状态。

        :return: ``None``。
        """
        # 用于保存所有子线程的引用
        self.threads = []

        # 用于保存每个节点的运行信息
        self.stage_dict = {}

        # 用于保存每个节点的上一次collect_runtime_snapshot()的状态信息
        self.status_dict = defaultdict(dict)

        # 用于保存最近一次状态快照对应的统一时间戳
        self.status_timestamp = 0.0

        # 用于保存每个节点的输入任务ID集合
        self.input_ids = defaultdict(set)

        # 用于保存源节点列表（由 _build_analysis 自动计算）
        self.source_stages = []

        # 用于保存图结构的邻接表
        self.out_edges = defaultdict(list)
        self.in_edges = defaultdict(list)
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

                self.out_edges[from_name].append(to_name)
                self.in_edges[to_name].append(from_name)

        self._analysis_dirty = True

    # ==== 配置 ====

    def _set_name(self, name: str) -> None:
        """
        设置任务图名称

        :param name: 任务图名称
        """
        self.name = name
        self.graph_id = f"{name}@{int(time.time() * 1000)}"

    def _set_schedule_mode(self, schedule_mode: str) -> None:
        """
        设置任务链的执行模式

        :param schedule_mode: 节点执行模式, 可选值为 'eager' 或 'staged'
        :raises ScheduleModeError: schedule_mode 不是 'eager' 或 'staged'
        """
        if schedule_mode == "eager":
            self.schedule_mode = "eager"
        elif schedule_mode == "staged":
            self.schedule_mode = "staged"
        else:
            raise ScheduleModeError(schedule_mode)

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

    def set_graph_mode(self, stage_mode: str, execution_mode: str) -> None:
        """
        设置任务链的执行模式

        :param stage_mode: 节点执行模式, 可选值为 'serial' 或 'thread'
        :param execution_mode: 节点内部执行模式, 可选值为 'serial', 'thread' 或 'async'
        """
        for stage in self.stage_dict.values():
            stage.set_stage_mode(stage_mode)
            stage.set_execution_mode(execution_mode)
        self._build_analysis()

    # ==== 启动 ====

    def _ensure_analysis(self) -> None:
        """按需重建图分析缓存。"""
        if self._analysis_dirty:
            self._build_analysis()

    def _build_analysis(self) -> None:
        """
        分析任务图，计算源节点、是否为 DAG 与层级信息。

        :return: ``None``。
        """
        source_names = source_nodes(self.order_graph)
        self.source_stages = [self.stage_dict[name] for name in source_names]

        self.structure_graph = build_structure_graph(
            self.stage_dict, self.out_edges, self.source_stages
        )

        self.is_dag = is_dag(self.order_graph)

        stage_level_dict = compute_node_levels(self.order_graph)
        self.layers_dict = cluster_by_value_sorted(stage_level_dict)
        self._analysis_dirty = False

    def put_stage_queue(
        self,
        tasks_dict: Mapping[str, Iterable[Any]],
        put_termination_signal: bool = True,
    ) -> None:
        """
        将任务放入队列

        :param tasks_dict: 待处理的任务字典
        :param put_termination_signal: 是否放入终止信号，默认 True
        :raises NodeNotFoundError: tasks_dict 中包含图中不存在的 stage 名称时抛出
        """
        for name, tasks in tasks_dict.items():
            if name not in self.stage_dict:
                raise NodeNotFoundError(f"unknown stage name: {name}")
            stage: AnyTaskStage = self.stage_dict[name]

            for task in tasks:
                if isinstance(task, TerminationSignal):
                    stage.put_signal()
                else:
                    stage.put_task(task)

        if not put_termination_signal:
            return

        for source_stage in self.source_stages:
            source_stage.put_signal()

    # ==== 执行 ====

    def _prepare_start_graph(
        self,
        init_tasks_dict: Mapping[str, Iterable[Any]],
        put_termination_signal: bool = True,
    ) -> None:
        """
        启动前准备：图分析、非 DAG 警告、启动运行时资源并注入任务。

        本方法会创建线程与文件句柄等运行时资源，调用方应保证在 finally 中
        执行 :meth:`_finish_start_graph` 完成收尾。

        :param init_tasks_dict: 任务列表
        :param put_termination_signal: 是否注入终止信号，默认 True
        :return: ``None``
        """
        self._build_analysis()

        if not self.is_dag and put_termination_signal:
            warnings.warn(
                (
                    "Early injection of termination signals in a non-DAG graph may cause "
                    "some nodes (including source nodes) to shut down as soon as their current "
                    "tasks are exhausted, preventing them from consuming tasks that arrive "
                    "later from other nodes. It is recommended to set put_termination_signal=False "
                    "and manually inject termination signals at an appropriate time."
                ),
                RuntimeWarning,
                stacklevel=2,
            )

        get_fallback_spout().start()
        get_log_spout().start()
        get_log_inlet().start_graph(self.name, self.get_structure_list())
        self.reporter.start()

        self.put_stage_queue(init_tasks_dict, put_termination_signal)

    def _finish_start_graph(self, start_perf: float) -> list[Exception]:
        """
        启动后收尾：停止上报器、记录图结束日志并关闭 spout。

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

        try:
            get_log_spout().stop()
        except Exception as exception:
            error_list.append(exception)
        try:
            get_fallback_spout().stop()
        except Exception as exception:
            error_list.append(exception)

        return error_list

    def start_graph(
        self,
        init_tasks_dict: Mapping[str, Iterable[Any]],
        put_termination_signal: bool = True,
    ) -> None:
        """
        启动任务链

        :param init_tasks_dict: 任务列表
        :param put_termination_signal: 是否注入终止信号，默认 True
        :note:
            TaskGraph 为一次性对象；当前实例启动并运行完成后，不保证可安全再次调用
            start_graph()。如需重复执行，请创建新的 TaskGraph 实例。
        """
        start_perf = time.perf_counter()
        self.start_time = time.time()
        error_list: list[Exception] = []
        try:
            self._prepare_start_graph(init_tasks_dict, put_termination_signal)
            self._execute_stages()
        except Exception as exception:
            error_list.append(exception)
        finally:
            error_list.extend(self._finish_start_graph(start_perf))

        if error_list:
            raise ExceptionGroup("Errors occurred during graph execution", error_list)

    async def start_graph_async(
        self,
        init_tasks_dict: Mapping[str, Iterable[Any]],
        put_termination_signal: bool = True,
    ) -> None:
        """
        以异步方式启动任务图，适合在已运行事件循环的上下文中调用。

        与 :meth:`start_graph` 的区别：
        - async 执行模式的节点通过 :meth:`TaskStage.start_stage_async` 以协程方式运行，
          不再内部调用 ``asyncio.run``，避免嵌套事件循环导致的崩溃。
        - serial / thread 执行模式的节点通过 ``asyncio.to_thread`` 在独立线程中运行，
          避免阻塞事件循环。

        :param init_tasks_dict: 任务列表
        :param put_termination_signal: 是否注入终止信号，默认 True
        :note:
            TaskGraph 为一次性对象；当前实例启动并运行完成后，不保证可安全再次调用
            start_graph_async()。如需重复执行，请创建新的 TaskGraph 实例。
        """
        start_perf = time.perf_counter()
        self.start_time = time.time()
        error_list: list[Exception] = []
        try:
            self._prepare_start_graph(init_tasks_dict, put_termination_signal)
            await self._execute_stages_async()
        except Exception as exception:
            error_list.append(exception)
        finally:
            error_list.extend(self._finish_start_graph(start_perf))

        if error_list:
            raise ExceptionGroup("Errors occurred during graph execution", error_list)

    def start_graph_db(
        self,
        db_path: str | Path,
        statuses: Iterable[str] | None = None,
        *,
        filter_by_error_type: bool = False,
        put_termination_signal: bool = True,
    ) -> None:
        """
        从 sqlite 持久化库中读取任务，按 stage 分组后启动任务图。

        :param db_path: sqlite 数据库文件路径
        :param statuses: 记录状态过滤列表，默认 ``["failed", "pending"]``
        :param filter_by_error_type: 是否按各 stage 的 ``retry_exceptions`` 过滤
            ``error_type``，默认 ``False``
        :param put_termination_signal: 是否注入终止信号，默认 True
        """
        statuses = ["failed", "pending"] if statuses is None else statuses
        grouped_records = load_tasks_grouped_by_stage(db_path, statuses)
        grouped_tasks: dict[str, list[Any]] = {}

        for name, records in grouped_records.items():
            if filter_by_error_type and name in self.stage_dict:
                stage = self.stage_dict[name]
                retry_error_type_names = stage.metrics.get_retry_error_type_names()
                records = [
                    record
                    for record in records
                    if str(record["error_type"]) in retry_error_type_names
                    or record["status"] == "pending"
                ]

            stage_tasks = [record["task_json"] for record in records]
            if stage_tasks:
                grouped_tasks[name] = stage_tasks

        self.start_graph(
            grouped_tasks,
            put_termination_signal=put_termination_signal,
        )

    def _execute_stages(self) -> None:
        """
        执行所有节点
        """
        if self.schedule_mode == "eager":
            # eager 调度模式：一次性执行所有节点
            for stage in self.stage_dict.values():
                self._execute_stage(stage)

            for t in self.threads:
                t.join()
        elif self.schedule_mode == "staged":
            # staged 调度模式：按层顺序执行
            for layer_level, layer in self.layers_dict.items():
                get_log_inlet().start_layer(layer, layer_level)
                start_perf = time.perf_counter()

                threads: list[threading.Thread] = []
                for stage_name in layer:
                    stage: AnyTaskStage = self.stage_dict[stage_name]
                    self._execute_stage(stage)
                    if stage.stage_mode == "thread":
                        threads.append(self.threads[-1])

                # 等待当前层的所有线程结束
                for t in threads:
                    t.join()

                get_log_inlet().end_layer(layer, time.perf_counter() - start_perf)

    async def _execute_stages_async(self) -> None:
        """
        异步执行所有节点：eager 全并发，staged 逐层执行。
        """
        if self.schedule_mode == "eager":
            tasks = [
                asyncio.create_task(self._execute_stage_async(stage))
                for stage in self.stage_dict.values()
            ]
            await asyncio.gather(*tasks)
        elif self.schedule_mode == "staged":
            for layer_level, layer in self.layers_dict.items():
                get_log_inlet().start_layer(layer, layer_level)
                start_perf = time.perf_counter()
                tasks = [
                    asyncio.create_task(
                        self._execute_stage_async(self.stage_dict[name])
                    )
                    for name in layer
                ]
                await asyncio.gather(*tasks)
                get_log_inlet().end_layer(layer, time.perf_counter() - start_perf)

    def _execute_stage(self, stage: AnyTaskStage) -> None:
        """
        执行单个节点

        :param stage: 节点
        :raises StageModeError: stage.stage_mode 不是 'serial' 或 'thread' 时抛出
        """
        if stage.stage_mode == "thread":
            t = threading.Thread(
                target=stage.start_stage,
                args=(),
                name=stage.get_name(),
                daemon=True,
            )
            t.start()
            self.threads.append(t)
        elif stage.stage_mode == "serial":
            stage.start_stage()
        else:
            raise StageModeError(stage.stage_mode)

    async def _execute_stage_async(self, stage: AnyTaskStage) -> None:
        """
        异步执行单个节点：async 模式走协程，其余模式走线程池。

        :param stage: 节点
        """
        if stage.execution_mode == "async":
            await stage.start_stage_async()
        else:
            await asyncio.to_thread(stage.start_stage)

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

        :return: 包含 name, startTime, is_dag, schedule_mode, class_name, layers_dict 的字典
        """
        self._ensure_analysis()
        return {
            "graphId": self.graph_id,
            "name": self.name,
            "startTime": self.start_time,
            "className": self.__class__.__name__,
            "isDAG": self.is_dag,
            "scheduleMode": self.schedule_mode,
            "layersDict": self.layers_dict,
        }

    def get_structure_graph(self) -> dict[str, Any]:
        """
        获取任务图的 JSON 结构

        :return: JSON 格式的任务图结构字典
        """
        self._ensure_analysis()
        return self.structure_graph

    def get_structure_list(self) -> list[str]:
        """
        获取任务图的格式化结构列表

        :return: 带边框的格式化字符串列表
        """
        self._ensure_analysis()
        return format_structure_list_from_graph(self.structure_graph)

    def get_source_stages(self) -> list[AnyTaskStage]:
        """
        获取源节点列表

        :return: 源节点列表
        """
        self._ensure_analysis()
        return self.source_stages

    def get_order_graph(self) -> OrderGraph:
        """
        获取任务图对应的有序有向图视图。

        :return: :class:`OrderGraph` 实例
        """
        return self.order_graph

    def get_fallback_path(self) -> Path:
        """
        获取失败任务的回退路径

        :return: 失败任务持久化文件的绝对路径，未设置时返回空 Path
        """
        db_path = get_fallback_spout().db_path
        if db_path is None:
            return Path()
        return Path(db_path).resolve()
