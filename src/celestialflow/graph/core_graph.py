# graph/core_graph.py
from __future__ import annotations

import threading
import time
import warnings
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from celestialtree import Client as CelestialTreeClient
from celestialtree import NullClient as NullCelestialTreeClient
from celestialtree import (
    format_descendants_forest,
)
from networkx import DiGraph, is_directed_acyclic_graph

from ..observability import NullTaskReporter, TaskReporter
from ..persistence import FailInlet, FailSpout, LogInlet, LogSpout
from ..persistence.util_jsonl import load_task_by_error, load_task_by_stage
from ..runtime import TaskInQueue, TaskOutQueue
from ..runtime.util_constant import LEVEL_DICT, STAGE_STYLE
from ..runtime.util_errors import (
    CelestialTreeConnectionError,
    DuplicateNodeError,
    LogLevelError,
    RuntimeStateError,
    ScheduleModeError,
)
from ..runtime.util_estimators import (
    calc_elapsed,
    calc_global_pending,
    calc_remaining,
)
from ..runtime.util_types import TerminationSignal
from ..stage import TaskStage
from ..utils.util_collections import cluster_by_value_sorted
from ..utils.util_format import format_avg_time
from .util_analysis import (
    build_networkx_graph,
    compute_node_levels,
    find_source_nodes,
)
from .util_serialize import build_structure_graph, format_structure_list_from_graph


class TaskGraph:
    """任务图核心类，负责构建、连接和调度一组 TaskStage 节点。

    注意：
    - TaskGraph 是一次性对象，设计上只应启动一次。
    - start_graph() 执行后，内部会建立并持有运行期资源、队列绑定和线程状态，
      不保证可被安全重置或重复启动。
    - 如需再次运行相同流程，请重新创建 TaskGraph 实例及其关联的 TaskStage。
    """

    # ==== 初始化 ====

    def __init__(
        self,
        schedule_mode: str = "eager",
        log_level: str = "INFO",
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

        :param schedule_mode: str, optional, default = 'eager'
            控制任务图的调度布局模式，支持以下两种策略：
            - 'eager'：
                默认模式。所有节点一次性调度并发执行，依赖关系通过队列流自动控制。
                适用于最大化并行度的执行场景。
            - 'staged'：
                分层执行模式。任务图必须为有向无环图（DAG）。
                节点按层级顺序逐层启动，确保上层所有任务完成后再启动下一层。
                更利于调试、性能分析和阶段性资源控制。

        :param log_level: str, optional, default = 'INFO'
            日志级别，支持以下级别：
            - 'TRACE'
            - 'DEBUG'
            - 'SUCCESS'
            - 'INFO'
            - 'WARNING'
            - 'ERROR'
            - 'CRITICAL'
        """
        self._set_log_level(log_level)
        self._set_schedule_mode(schedule_mode)
        self.set_reporter()
        self.set_ctree()

        self._init_env()

    def _init_env(self) -> None:
        """
        初始化环境
        """
        self._init_state()
        self._init_spout()
        self._init_inlet()

    def _init_state(self) -> None:
        """
        初始化状态
        """
        # 用于保存所有子线程的引用
        self.threads: list[threading.Thread] = []
        # 用于保存每个节点的运行信息
        self.stage_dict: dict[str, TaskStage] = {}
        # 用于保存每个节点的上一次collect_runtime_snapshot()的状态信息
        self.status_dict: dict[str, dict[str, Any]] = defaultdict(dict)
        # 用于保存最近一次状态快照对应的统一时间戳
        self.status_timestamp: float = 0.0
        # 用于保存每个节点的输入任务ID集合
        self.input_ids: dict[str, set[int]] = defaultdict(set)
        # 用于保存源节点列表（由 _build_analysis 自动计算）
        self.source_stages: list[TaskStage] = []
        # 用于保存图结构的邻接表
        self.out_edges: dict[str, list[str]] = defaultdict(list)
        self.in_edges: dict[str, list[str]] = defaultdict(list)

    def _init_spout(self) -> None:
        """
        初始化监听器
        """
        self.log_spout = LogSpout()
        self.fail_spout = FailSpout("graph_errors")

    def _init_inlet(self) -> None:
        """
        初始化收集器
        """
        self.log_inlet = LogInlet(self.log_spout.get_queue(), self.log_level)
        self.fail_inlet = FailInlet(self.fail_spout.get_queue())

    # ==== 建图 ====

    def set_stages(self, stages: list[TaskStage]) -> None:
        """
        添加节点到任务图中

        :param stages: 待添加的节点列表
        :raises DuplicateNodeError: 存在重复的 stage 名称
        """
        fail_queue = self.fail_spout.get_queue()
        log_queue = self.log_spout.get_queue()

        for stage in stages:
            stage_name = stage.get_name()
            if stage_name in self.stage_dict:
                raise DuplicateNodeError(f"duplicate stage name: {stage_name}")

            self.stage_dict[stage_name] = stage

            stage.set_inlet(fail_queue, log_queue)

    def connect(self, from_stages: list[TaskStage], to_stages: list[TaskStage]) -> None:
        """
        建立超边连接：from_stages 中的每个节点连接到 to_stages 中的每个节点。

        :param from_stages: 上游节点列表
        :param to_stages: 下游节点列表
        """
        for from_stage in from_stages:
            for to_stage in to_stages:
                self.out_edges[from_stage.get_name()].append(to_stage.get_name())
                self.in_edges[to_stage.get_name()].append(from_stage.get_name())

    # ==== 配置 ====

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

    def _set_log_level(self, level: str = "INFO") -> None:
        """
        设置日志级别

        :param level: 日志级别, 默认为 "INFO"
        """
        self.log_level = level.upper()
        if self.log_level not in LEVEL_DICT:
            raise LogLevelError(self.log_level)

    def set_reporter(
        self, is_report: bool = False, host: str = "127.0.0.1", port: int = 5000
    ) -> None:
        """
        设定报告器

        :param is_report: 是否启用报告器，默认 False
        :param host: 报告器主机地址，默认 "127.0.0.1"
        :param port: 报告器端口，默认 5000
        """
        self.is_report = is_report
        self.report_host = host
        self.report_port = port
        self.reporter: TaskReporter | NullTaskReporter
        if is_report:
            self.reporter = TaskReporter(
                host=host,
                port=port,
                task_graph=self,
                log_inlet=self.log_inlet,
            )
        else:
            self.reporter = NullTaskReporter()

    def set_ctree(
        self,
        use_ctree: bool = False,
        host: str = "127.0.0.1",
        http_port: int = 7777,
        grpc_port: int = 7778,
        transport: str = "grpc",
    ) -> None:
        """
        设定事件树客户端

        :param use_ctree: 是否使用事件树，默认 False
        :param host: 事件树主机地址，默认 "127.0.0.1"
        :param http_port: 事件树 HTTP 端口，默认 7777
        :param grpc_port: 事件树 gRPC 端口，默认 7778
        :param transport: 传输方式, 可选 'grpc' 或 'http'，默认 'grpc'
        :raises CelestialTreeConnectionError: 使用 ctree 但 health check 失败
        """
        self.use_ctree = use_ctree
        self.ctree_host = host
        self.ctree_http_port = http_port
        self.ctree_grpc_port = grpc_port
        self.ctree_transport = transport

        self.ctree_client: CelestialTreeClient | NullCelestialTreeClient
        if use_ctree:
            self.ctree_client = CelestialTreeClient(
                host=host, http_port=http_port, grpc_port=grpc_port, transport=transport
            )
            if not self.ctree_client.health():
                raise CelestialTreeConnectionError()
        else:
            self.ctree_client = NullCelestialTreeClient()

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

    def _build_resources(self) -> None:
        """
        构建每个阶段的运行时资源（队列、计数器、前驱绑定）
        """
        for stage_name, current_stage in self.stage_dict.items():
            if not self.in_edges[stage_name]:  # 如果没有前驱
                continue

            in_queue: TaskInQueue = current_stage.task_queue
            prev_stages: list[TaskStage] = []

            # 遍历每个前驱，创建边队列
            for prev_stage_name in self.in_edges[stage_name]:
                in_queue.add_source_name(prev_stage_name)

                prev_stage = self.stage_dict[prev_stage_name]
                prev_out_queue: TaskOutQueue = prev_stage.result_queue
                prev_out_queue.add_queue(in_queue.queue, stage_name)
                prev_stages.append(prev_stage)

            current_stage.prev_bindings(prev_stages)

    def _build_analysis(self) -> None:
        """
        分析任务图，计算图属性和层级信息（支持 DAG 和含环图）
        """
        self.networkx_graph = build_networkx_graph(self.out_edges, self.stage_dict)
        source_names = find_source_nodes(self.networkx_graph)
        self.source_stages = [self.stage_dict[name] for name in source_names]

        self.structure_graph = build_structure_graph(
            self.stage_dict, self.out_edges, self.source_stages
        )

        self.is_dag = is_directed_acyclic_graph(self.networkx_graph)

        stage_level_dict = compute_node_levels(self.networkx_graph)
        self.layers_dict = cluster_by_value_sorted(stage_level_dict)

    def put_stage_queue(
        self,
        tasks_dict: Mapping[str, Iterable[Any]],
        put_termination_signal: bool = True,
    ) -> None:
        """
        将任务放入队列

        :param tasks_dict: 待处理的任务字典
        :param put_termination_signal: 是否放入终止信号，默认 True
        """
        for name, tasks in tasks_dict.items():
            if name not in self.stage_dict:
                continue
            stage: TaskStage = self.stage_dict[name]

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
        self._build_resources()
        self._build_analysis()

        if not self.is_dag and put_termination_signal:
            warnings.warn(
                (
                    "Early injection of termination signals in a non-DAG graph may cause "
                    "some nodes (including source nodes) to shut down as soon as their current "
                    "tasks are exhausted, preventing them from consuming tasks that arrive "
                    "later from other nodes. It is recommended to set put_termination_signal=False "
                    "and manually inject termination signals via the web interface at an "
                    "appropriate time."
                ),
                RuntimeWarning,
                stacklevel=2,
            )
        start_time = time.perf_counter()

        try:
            self.fail_spout.start()
            self.log_spout.start()
            self.log_inlet.start_graph(self.get_structure_list())
            self.fail_inlet.start_graph(self.get_structure_graph())
            self.reporter.start()

            self.put_stage_queue(init_tasks_dict, put_termination_signal)
            self._execute_stages()

        finally:
            self._finalize_nodes()

            self.reporter.stop()
            self.log_inlet.end_graph(time.perf_counter() - start_time)
            self.fail_spout.stop()
            self.log_spout.stop()

    def _execute_stages(self) -> None:
        """
        执行所有节点
        """
        if self.schedule_mode == "eager":
            # eager schedule_mode：一次性执行所有节点
            for stage in self.stage_dict.values():
                self._execute_stage(stage)

            for t in self.threads:
                t.join()
        elif self.schedule_mode == "staged":
            # staged schedule_mode：一层层地顺序执行
            for layer_level, layer in self.layers_dict.items():
                self.log_inlet.start_layer(layer, layer_level)
                start_time = time.perf_counter()

                threads: list[threading.Thread] = []
                for stage_name in layer:
                    stage: TaskStage = self.stage_dict[stage_name]
                    self._execute_stage(stage)
                    if stage.stage_mode == "thread":
                        threads.append(self.threads[-1])

                # join 当前层的所有线程
                for t in threads:
                    t.join()

                self.log_inlet.end_layer(layer, time.perf_counter() - start_time)

    def _execute_stage(self, stage: TaskStage) -> None:
        """
        执行单个节点

        :param stage: 节点
        """
        if self.use_ctree:
            stage.set_ctree(self.ctree_host, self.ctree_http_port, self.ctree_grpc_port)
        else:
            stage.set_nullctree(self.ctree_client.event_id)

        stage.set_log_level(self.log_level)

        if stage.stage_mode == "thread":
            t = threading.Thread(
                target=stage.start_stage,
                args=(),
                name=stage.get_name(),
                daemon=True,
            )
            t.start()
            self.threads.append(t)
        else:
            stage.start_stage()

    # ==== 终止与清理 ====

    def _finalize_nodes(self) -> None:
        """
        确保所有线程安全结束，更新节点状态，并导出每个节点队列剩余任务。
        """
        # 确保所有线程安全结束（线程不可 terminate，仅做 cooperative join）
        alive_thread_names: list[str] = []
        for t in self.threads:
            t.join(timeout=10)
            if t.is_alive():
                alive_thread_names.append(t.name)

        if alive_thread_names:
            stage_names = ", ".join(sorted(alive_thread_names))
            raise RuntimeStateError(
                "TaskGraph shutdown incomplete; alive stage threads remain after finalize: "
                f"{stage_names}"
            )

        # 更新所有节点状态为"已停止"
        for stage in self.stage_dict.values():
            stage.mark_stopped()

        # 收集并持久化每个 stage 中未消费的任务
        for stage in self.stage_dict.values():
            stage.drain_task_queue()

        self.collect_runtime_snapshot()

    # ==== 运行时监控 ====

    def _snapshot_one_stage(
        self,
        stage: TaskStage,
        last_status: dict[str, Any],
        interval: float,
    ) -> tuple[dict[str, Any], tuple[int, int]]:
        """
        计算单个 stage 的运行时快照
        :param stage: 节点实例
        :param last_status: 上一次快照的状态字典（用于累计 elapsed_time）
        :param interval: 快照采集间隔
        :return: (stage_snapshot_dict, running_metrics)，其中
            running_metrics = (processed, pending, elapsed, remaining)
        """
        status = stage.get_status()
        stage_counts = stage.get_counts()

        start_time = stage.start_time
        last_elapsed: float = float(last_status.get("elapsed_time", 0))
        last_pending: int = int(last_status.get("tasks_pending", 0))
        elapsed = calc_elapsed(status, last_elapsed, last_pending, interval)

        remaining = calc_remaining(
            stage_counts["tasks_processed"], stage_counts["tasks_pending"], elapsed
        )

        # 计算平均时间（秒/任务）并格式化为字符串
        avg_time_str = format_avg_time(elapsed, stage_counts["tasks_processed"])

        snapshot: dict[str, Any] = {
            **stage.get_summary(),
            "status": status,
            **stage_counts,
            "start_time": start_time,
            "elapsed_time": elapsed,
            "remaining_time": remaining,
            "task_avg_time": avg_time_str,
        }

        processed = int(stage_counts["tasks_processed"] or 0)
        pending = int(stage_counts["tasks_pending"] or 0)

        return snapshot, (processed, pending)

    def _calc_graph_pending(
        self,
        running_processed_map: dict[str, int],
        running_pending_map: dict[str, int],
    ) -> dict[str, int]:
        """
        根据 DAG/非 DAG 策略计算全局预计待处理任务数量

        :param running_processed_map: 各节点已处理任务数
        :param running_pending_map: 各节点待处理任务数
        :return: 全局预计待处理任务数量
        """
        if not self.is_dag:
            return running_pending_map

        total_pending_map = calc_global_pending(
            self.networkx_graph,
            running_processed_map,
            running_pending_map,
        )
        return total_pending_map

    def collect_runtime_snapshot(self) -> None:
        """
        收集运行时快照
        """
        status_dict: dict[str, dict[str, Any]] = {}
        now = time.time()
        interval = self.reporter.interval

        # 为全局预计 tasks_pending 收集数据
        running_processed_map: dict[str, int] = {}
        running_pending_map: dict[str, int] = {}

        for stage_name, stage in self.stage_dict.items():
            last_status = self.status_dict.get(stage_name, {})

            snapshot, (processed, pending) = self._snapshot_one_stage(
                stage,
                last_status,
                interval,
            )

            status_dict[stage_name] = snapshot

            # 更新各节点的 processed, pending, remaining 数据
            running_processed_map[stage_name] = processed
            running_pending_map[stage_name] = pending

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

    def get_fail_by_stage_dict(self) -> dict[str, list[Any]]:
        """
        获取按节点分组的失败任务字典

        :return: {stage_name: [失败任务列表]}
        """
        if self.fail_spout.jsonl_path is None:
            return {}
        return load_task_by_stage(self.fail_spout.jsonl_path)

    def get_fail_by_error_dict(self) -> dict[tuple[str, ...], list[Any]]:
        """
        获取按错误类型分组的失败任务字典

        :return: {error_type: [失败任务列表]}
        """
        if self.fail_spout.jsonl_path is None:
            return {}
        return load_task_by_error(self.fail_spout.jsonl_path)

    def get_total_error_num(self) -> int:
        """
        获取总错误数

        :return: 错误总数
        """
        return self.fail_spout.total_error_num

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

        :return: 包含 is_dag, schedule_mode, class_name, layers_dict 的字典
        """
        return {
            "isDAG": self.is_dag,
            "scheduleMode": self.schedule_mode,
            "className": self.__class__.__name__,
            "layersDict": self.layers_dict,
        }

    def get_structure_graph(self) -> dict[str, Any]:
        """
        获取任务图的 JSON 结构

        :return: JSON 格式的任务图结构字典
        """
        return self.structure_graph

    def get_structure_list(self) -> list[str]:
        """
        获取任务图的格式化结构列表

        :return: 带边框的格式化字符串列表
        """
        return format_structure_list_from_graph(self.structure_graph)

    def get_networkx_graph(self) -> DiGraph[Any]:
        """
        获取任务图的 networkx 有向图（DiGraph）

        :return: networkx.DiGraph 实例
        """
        return self.networkx_graph

    def get_fallback_path(self) -> str:
        """
        获取失败任务的回退路径

        :return: 失败任务 JSONL 文件的绝对路径，未设置时返回空字符串
        """
        if self.fail_spout.jsonl_path is None:
            return ""
        return str(Path(self.fail_spout.jsonl_path).resolve())

    def get_stage_input_trace(self, stage_name: str) -> str:
        """
        获取任务节点的输入依赖关系树

        :param stage_name: 节点唯一名称
        :return: 格式化的依赖关系树字符串
        """
        if not self.use_ctree:
            return ""

        input_ids: set[int] = self.input_ids[stage_name]
        descendants = self.ctree_client.descendants_batch(list(input_ids), "meta")
        if not descendants:
            return ""
        return format_descendants_forest(descendants, STAGE_STYLE)

    def get_source_stages(self) -> list[TaskStage]:
        """
        获取源节点列表

        :return: 源节点列表
        """
        self._build_analysis()  # 确保 source_stages 已更新
        return self.source_stages
