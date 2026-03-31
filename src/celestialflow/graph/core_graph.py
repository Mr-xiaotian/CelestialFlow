# graph/core_graph.py
import multiprocessing
import time
import warnings
from collections import defaultdict, deque
from pathlib import Path
from typing import Any
from multiprocessing import Queue as MPQueue

from celestialtree import (
    Client as CelestialTreeClient,
)
from celestialtree import (
    NullClient as NullCelestialTreeClient,
)
from celestialtree import (
    format_descendants_forest,
    format_provenance_forest,
)
from networkx import is_directed_acyclic_graph

from ..observability import NullTaskReporter, TaskReporter
from ..persistence import FailListener, FailSinker, LogListener, LogSinker
from ..persistence.util_jsonl import load_task_by_error, load_task_by_stage
from ..runtime import TaskEnvelope, TaskInQueue, TaskOutQueue
from ..runtime.util_errors import UnconsumedError
from ..runtime.util_estimators import (
    calc_elapsed,
    calc_global_remain_equal_pred,
    calc_remaining,
)
from ..runtime.util_types import (
    NULL_PREV_STAGE,
    STAGE_STYLE,
    StageStatus,
    TerminationSignal,
)
from ..stage import TaskStage
from ..utils.util_collections import cluster_by_value_sorted
from ..utils.util_format import format_avg_time
from .util_analysis import (
    compute_node_levels,
    format_networkx_graph,
)
from .util_serialize import build_structure_graph, format_structure_list_from_graph


class TaskGraph:
    def __init__(
        self,
        root_stages: list[TaskStage],
        schedule_mode: str = "eager",
        log_level: str = "SUCCESS",
    ) -> None:
        """
        初始化 TaskGraph 实例。

        TaskGraph 表示一组 TaskStage 节点所构成的任务图，可用于构建并行、串行、
        分层等多种形式的任务执行流程。通过分析图结构和调度布局策略，实现灵活的
        DAG 任务调度控制。

        :param root_stages: List[TaskStage]
            根节点 TaskStage 列表，用于构建任务图的入口节点。
            支持多根节点（森林结构），系统将自动构建整个任务依赖图。

        :param schedule_mode: str, optional, default = 'eager'
            控制任务图的调度布局模式，支持以下两种策略：
            - 'eager'：
                默认模式。所有节点一次性调度并发执行，依赖关系通过队列流自动控制。
                适用于最大化并行度的执行场景。
            - 'staged'：
                分层执行模式。任务图必须为有向无环图（DAG）。
                节点按层级顺序逐层启动，确保上层所有任务完成后再启动下一层。
                更利于调试、性能分析和阶段性资源控制。

        :param log_level: str, optional, default = 'SUCCESS'
            日志级别，支持以下级别：
            - 'TRACE'
            - 'DEBUG'
            - 'SUCCESS'
            - 'INFO'
            - 'WARNING'
            - 'ERROR'
            - 'CRITICAL'
        """
        self.set_root_stages(root_stages)
        self.set_log_level(log_level)
        self.set_reporter()
        self.set_ctree()

        self.init_env()
        self.set_schedule_mode(schedule_mode)

    def init_env(self) -> None:
        """
        初始化环境
        """
        self.init_state()
        self.init_listener()
        self.init_sinker()
        self.init_resources()
        self.init_analysis()

    def init_state(self) -> None:
        """
        初始化状态
        """
        # 用于保存所有子进程的引用
        self.processes: list[multiprocessing.Process] = []
        # 用于保存每个节点的运行信息
        self.stage_runtime_dict: dict[str, dict[str, Any]] = defaultdict(dict)
        # 用于保存每个节点的上一次collect_runtime_snapshot()的状态信息
        self.status_dict: dict[str, dict[str, Any]] = defaultdict(dict)
        # 用于保存任务图的摘要信息
        self.graph_summary: dict[str, int | float] = {}
        # 用于保存每个节点的历史状态信息列表（仅保留最近20条）
        self.stage_history: dict[str, list[dict]] = {}
        # 用于保存每个节点的输入任务ID集合
        self.input_ids: dict[str, set[int]] = defaultdict(set)

    def init_listener(self) -> None:
        """
        初始化监听器
        """
        self.log_listener = LogListener()
        self.fail_listener = FailListener("graph_errors")

    def init_sinker(self) -> None:
        """
        初始化收集器
        """
        self.log_sinker = LogSinker(self.log_listener.get_queue(), self.log_level)
        self.fail_sinker = FailSinker(self.fail_listener.get_queue())

    def init_resources(self) -> None:
        """
        初始化每个阶段资源
        """
        visited_stages = set()
        queue = deque(self.root_stages)

        # BFS 连接
        while queue:
            stage = queue.popleft()
            stage_tag = stage.get_tag()
            if stage_tag in visited_stages:
                continue
            stage_runtime = self.stage_runtime_dict[stage_tag]

            # 刷新所有 counter
            stage.metrics.reset_counter()

            # 记录节点
            stage_runtime["stage"] = stage

            stage_runtime["in_queue"] = TaskInQueue(
                queue=MPQueue(),
                queue_tags=[],
                out_tag=stage.get_tag(),
                log_sinker=self.log_sinker,
            )
            stage_runtime["out_queue"] = TaskOutQueue(
                queue_list=[],
                queue_tags=[],
                in_tag=stage.get_tag(),
                log_sinker=self.log_sinker,
            )

            visited_stages.add(stage_tag)
            queue.extend(stage.next_stages)

        for stage_tag, stage_runtime in self.stage_runtime_dict.items():
            current_stage: TaskStage = stage_runtime["stage"]
            in_queue: TaskInQueue = stage_runtime["in_queue"]

            # 遍历每个前驱，创建边队列
            for prev_stage in current_stage.prev_stages:
                prev_stage_tag = prev_stage.get_tag()
                in_queue.add_source_tag(prev_stage_tag)

                # source side
                if prev_stage != NULL_PREV_STAGE:
                    prev_out_queue: TaskOutQueue = self.stage_runtime_dict[
                        prev_stage_tag
                    ]["out_queue"]
                    prev_out_queue.add_queue(in_queue.queue, stage_tag)

    def init_analysis(self) -> None:
        """
        分析任务图，计算 DAG 属性和层级信息
        """
        self.structure_json = build_structure_graph(self.root_stages)
        self.structure_list = format_structure_list_from_graph(self.structure_json)
        self.networkx_graph = format_networkx_graph(self.structure_json)

        self.isDAG = is_directed_acyclic_graph(self.networkx_graph)
        self.layers_dict = {}
        if self.isDAG:
            stage_level_dict = compute_node_levels(self.networkx_graph)
            self.layers_dict = cluster_by_value_sorted(stage_level_dict)

    def set_root_stages(self, root_stages: list[TaskStage]) -> None:
        """
        设置根节点

        :param root_stages: 根节点列表
        """
        self.root_stages = root_stages
        for stage in root_stages:
            if not stage.prev_stages:
                stage.add_prev_stages(NULL_PREV_STAGE)

    def set_schedule_mode(self, schedule_mode: str) -> None:
        """
        设置任务链的执行模式

        :param schedule_mode: 节点执行模式, 可选值为 'eager' 或 'staged'
        """
        if schedule_mode == "eager":
            self.schedule_mode = "eager"
        elif schedule_mode == "staged" and self.isDAG:
            self.schedule_mode = "staged"
        elif schedule_mode == "staged" and not self.isDAG:
            raise Exception("The task graph is not a DAG, cannot use staged mode")
        else:
            raise Exception(
                f"Invalid schedule mode: {schedule_mode}. "
                "Valid options are 'eager' or 'staged'"
            )

    def set_reporter(
        self, is_report: bool = False, host: str = "127.0.0.1", port: int = 5000
    ) -> None:
        """
        设定报告器

        :param is_report: 是否启用报告器
        :param host: 报告器主机地址
        :param port: 报告器端口
        """
        self._is_report = is_report
        self._report_host = host
        self._report_port = port
        self.reporter: TaskReporter | NullTaskReporter
        if is_report:
            self.reporter = TaskReporter(
                host=host,
                port=port,
                task_graph=self,
                log_sinker=self.log_sinker,
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

        :param use_ctree: 是否使用事件树
        :param host: 事件树主机地址
        :param port: 事件树端口
        """
        self._use_ctree = use_ctree
        self._ctree_host = host
        self._CTREE_HTTP_PORT = http_port
        self._ctree_grpc_port = grpc_port
        self._ctree_transport = transport

        if use_ctree:
            self.ctree_client = CelestialTreeClient(
                host=host, http_port=http_port, grpc_port=grpc_port, transport=transport
            )
            if not self.ctree_client.health():
                raise Exception("CelestialTreeClient is not available")
        else:
            self.ctree_client = NullCelestialTreeClient()

    def set_log_level(self, level: str = "SUCCESS") -> None:
        """
        设置日志级别

        :param level: 日志级别, 默认为 "SUCCESS"
        """
        self.log_level = level.upper()

    def set_graph_mode(self, stage_mode: str, execution_mode: str) -> None:
        """
        设置任务链的执行模式

        :param stage_mode: 节点执行模式, 可选值为 'serial' 或 'process'
        :param execution_mode: 节点内部执行模式, 可选值为 'serial' 或 'thread''
        """

        def set_subsequent_stage_mode(stage: TaskStage) -> None:
            stage.set_stage_mode(stage_mode)
            stage.set_execution_mode(execution_mode)
            visited_stages.add(stage)

            for next_stage in stage.next_stages:
                if next_stage in visited_stages:
                    continue
                set_subsequent_stage_mode(next_stage)

        visited_stages: set[TaskStage] = set()
        for root_stage in self.root_stages:
            set_subsequent_stage_mode(root_stage)
        self.init_analysis()

    def put_stage_queue(
        self, tasks_dict: dict, put_termination_signal: bool = True
    ) -> None:
        """
        将任务放入队列

        :param tasks_dict: 待处理的任务字典
        :param put_termination_signal: 是否放入终止信号
        """
        for tag, tasks in tasks_dict.items():
            stage: TaskStage = self.stage_runtime_dict[tag]["stage"]
            in_queue: TaskInQueue = self.stage_runtime_dict[tag]["in_queue"]
            input_ids: set = self.input_ids[tag]

            for task in tasks:
                if isinstance(task, TerminationSignal):
                    termination_id = self.ctree_client.emit(
                        "termination.input",
                        payload=stage.get_summary(),
                    )
                    in_queue.put(TerminationSignal(termination_id, source="input"))
                    continue

                input_id = self.ctree_client.emit(
                    "task.input",
                    payload=stage.get_summary(),
                )
                envelope = TaskEnvelope.wrap(task, input_id, source="input")
                in_queue.put(envelope)
                input_ids.add(input_id)

                stage.metrics.add_task_count()
                self.log_sinker.task_input(
                    stage.get_func_name(),
                    stage.get_task_repr(task),
                    stage.get_tag(),
                    input_id,
                )

        if put_termination_signal:
            for root_stage in self.root_stages:
                root_stage_tag = root_stage.get_tag()
                root_in_queue: TaskInQueue = self.stage_runtime_dict[root_stage_tag][
                    "in_queue"
                ]

                termination_id = self.ctree_client.emit(
                    "termination.input",
                    payload=root_stage.get_summary(),
                )
                root_in_queue.put(TerminationSignal(termination_id, source="input"))
                self.log_sinker.termination_input(
                    root_stage.get_func_name(),
                    root_stage.get_tag(),
                    termination_id,
                )

    def start_graph(
        self, init_tasks_dict: dict, put_termination_signal: bool = True
    ) -> None:
        """
        启动任务链

        :param init_tasks_dict: 任务列表
        :param put_termination_signal: 是否注入终止信号
        """
        if self.isDAG == False and put_termination_signal == True:
            warnings.warn(
                "Early injection of termination signals in a non-DAG graph may cause "
                "some nodes (including root nodes) to shut down as soon as their current "
                "tasks are exhausted, preventing them from consuming tasks that arrive "
                "later from other nodes. It is recommended to set put_termination_signal=False "
                "and manually inject termination signals via the web interface at an "
                "appropriate time.",
                RuntimeWarning,
            )

        try:
            start_time = time.perf_counter()
            self.fail_listener.start()
            self.log_listener.start()
            self.log_sinker.start_graph(self.get_structure_list())
            self.fail_sinker.start_graph(self.get_structure_json())
            self.reporter.start()

            self.put_stage_queue(init_tasks_dict, put_termination_signal)
            self._excute_stages()

        finally:
            self.finalize_nodes()

            self.reporter.stop()
            self.release_resources()
            self.log_sinker.end_graph(time.perf_counter() - start_time)
            self.fail_listener.stop()
            self.log_listener.stop()

    def _excute_stages(self) -> None:
        """
        执行所有节点
        """
        if self.schedule_mode == "eager":
            # eager schedule_mode：一次性执行所有节点
            for stage_runtime in self.stage_runtime_dict.values():
                self._execute_stage(stage_runtime["stage"])

            for p in self.processes:
                p.join()
                self.log_sinker.process_exit(p.name, p.exitcode)
        elif self.schedule_mode == "staged":
            # staged schedule_mode：一层层地顺序执行
            for layer_level, layer in self.layers_dict.items():
                self.log_sinker.start_layer(layer, layer_level)
                start_time = time.perf_counter()

                processes = []
                for stage_tag in layer:
                    stage: TaskStage = self.stage_runtime_dict[stage_tag]["stage"]
                    self._execute_stage(stage)
                    if stage.stage_mode == "process":
                        processes.append(self.processes[-1])  # 最新的进程

                # join 当前层的所有进程（如果有）
                for p in processes:
                    p.join()
                    self.log_sinker.process_exit(p.name, p.exitcode)

                self.log_sinker.end_layer(layer, time.perf_counter() - start_time)

    def _execute_stage(self, stage: TaskStage) -> None:
        """
        执行单个节点

        :param stage: 节点
        """
        stage_tag = stage.get_tag()
        stage_runtime = self.stage_runtime_dict[stage_tag]

        fail_queue = self.fail_listener.get_queue()
        log_queue = self.log_listener.get_queue()

        # 输入输出队列
        input_queues: TaskInQueue = stage_runtime["in_queue"]
        output_queues: TaskOutQueue = stage_runtime["out_queue"]

        stage_runtime["start_time"] = time.time()

        if self._use_ctree:
            stage.set_ctree(
                self._ctree_host, self._CTREE_HTTP_PORT, self._ctree_grpc_port
            )
        else:
            stage.set_nullctree(self.ctree_client.event_id)

        stage.set_log_level(self.log_level)

        if stage.stage_mode == "process":
            p = multiprocessing.Process(
                target=stage.start_stage,
                args=(input_queues, output_queues, fail_queue, log_queue),
                name=stage_tag,
            )
            p.start()
            self.processes.append(p)
        else:
            stage.start_stage(input_queues, output_queues, fail_queue, log_queue)

    def finalize_nodes(self) -> None:
        """
        确保所有子进程安全结束，更新节点状态，并导出每个节点队列剩余任务。
        """
        # 确保所有进程安全结束（不一定要 terminate，但如果没结束就强制）
        for p in self.processes:
            if p.is_alive():
                self.log_sinker.process_termination_attempt(p.name)
                p.terminate()
                p.join(timeout=5)
                if p.is_alive():
                    self.log_sinker.process_termination_timeout(p.name)
                self.log_sinker.process_exit(p.name, p.exitcode)

        # 更新所有节点状态为“已停止”
        for stage_runtime in self.stage_runtime_dict.values():
            stage: TaskStage = stage_runtime["stage"]
            stage.mark_stopped()

        # 收集并持久化每个 stage 中未消费的任务
        for stage_tag, stage_runtime in self.stage_runtime_dict.items():
            current_stage: TaskStage = stage_runtime["stage"]
            in_queue: TaskInQueue = stage_runtime["in_queue"]

            remaining_sources = in_queue.drain()
            stage.metrics.add_error_count(len(remaining_sources))

            # 持久化逻辑
            for source in remaining_sources:
                task = source.task
                task_id = source.id
                error_id = self.ctree_client.emit(
                    "task.error",
                    [task_id],
                    payload=current_stage.get_summary(),
                )

                self.fail_sinker.task_error(
                    stage_tag, UnconsumedError(), error_id, task
                )

                self.log_sinker.task_error(
                    current_stage.get_func_name(),
                    current_stage.get_task_repr(task),
                    UnconsumedError(),
                    task_id,
                    error_id,
                )

    def release_resources(self) -> None:
        """
        释放资源
        """
        for stage_runtime in self.stage_runtime_dict.values():
            stage: TaskStage = stage_runtime["stage"]
            stage.release_queue()

    def collect_runtime_snapshot(self) -> None:
        """
        收集运行时快照
        """
        status_dict = {}
        now = time.time()
        interval = self.reporter.interval
        history_limit = self.reporter.history_limit

        totals = {
            "total_successed": 0,
            "total_pending": 0,
            "total_failed": 0,
            "total_duplicated": 0,
            "total_nodes": 0,  # running nodes
            "total_remain": 0.0,
        }

        # 为全局预计 remaining 收集
        running_elapsed_map: dict[str, float] = {}
        running_processed_map: dict[str, int] = {}
        running_pending_map: dict[str, int] = {}
        running_remaining_map: dict[str, float] = {}

        history_dict: dict[str, list[dict]] = {}

        for stage_tag, stage_runtime in self.stage_runtime_dict.items():
            stage: TaskStage = stage_runtime["stage"]
            last_stage_status_dict: dict = self.status_dict.get(stage_tag, {})

            status = stage.get_status()

            stage_counts = stage.get_counts()

            totals["total_successed"] += stage_counts["tasks_successed"]
            totals["total_pending"] += stage_counts["tasks_pending"]
            totals["total_failed"] += stage_counts["tasks_failed"]
            totals["total_duplicated"] += stage_counts["tasks_duplicated"]

            keys = [
                "tasks_successed",
                "tasks_pending",
                "tasks_failed",
                "tasks_duplicated",
                "tasks_processed",
            ]
            deltas = {
                f"add_{k}": stage_counts[k] - last_stage_status_dict.get(k, 0)
                for k in keys
            }

            start_time = stage_runtime.get("start_time", 0)
            last_elapsed = last_stage_status_dict.get("elapsed_time", 0)
            last_pending = last_stage_status_dict.get("tasks_pending", 0)
            elapsed = calc_elapsed(status, last_elapsed, last_pending, interval)

            # 估算剩余时间
            remaining = calc_remaining(
                stage_counts["tasks_processed"], stage_counts["tasks_pending"], elapsed
            )

            if status == StageStatus.RUNNING:
                totals["total_nodes"] += 1

            running_processed_map[stage_tag] = int(stage_counts["tasks_processed"] or 0)
            running_pending_map[stage_tag] = int(stage_counts["tasks_pending"] or 0)
            running_elapsed_map[stage_tag] = float(elapsed or 0.0)
            running_remaining_map[stage_tag] = float(remaining or 0.0)

            # 计算平均时间（秒/任务）并格式化为字符串
            avg_time_str = format_avg_time(elapsed, stage_counts["tasks_processed"])

            history: list = list(self.stage_history.get(stage_tag, []))
            history.append(
                {
                    "timestamp": now,
                    "tasks_processed": stage_counts["tasks_processed"],
                }
            )
            history.pop(0) if len(history) > history_limit else None
            history_dict[stage_tag] = history

            status_dict[stage_tag] = {
                **stage.get_summary(),
                "status": status,
                **stage_counts,
                **deltas,
                "start_time": start_time,
                "elapsed_time": elapsed,
                "remaining_time": remaining,
                "task_avg_time": avg_time_str,
            }

        if not self.isDAG:
            totals["total_remain"] = max(running_remaining_map.values(), default=0.0)
        else:
            expected_pending_map = calc_global_remain_equal_pred(
                self.networkx_graph,
                running_processed_map,
                running_pending_map,
                running_elapsed_map,
            )
            totals["total_remain"] = max(expected_pending_map.values(), default=0.0)

        self.status_dict = status_dict
        self.graph_summary = dict(totals)
        self.stage_history = dict(history_dict)

    def get_fail_by_stage_dict(self) -> dict:
        return load_task_by_stage(self.fail_listener.jsonl_path)

    def get_fail_by_error_dict(self) -> dict:
        return load_task_by_error(self.fail_listener.jsonl_path)
    
    def get_total_error_num(self) -> int:
        return self.fail_listener.total_error_num

    def get_status_dict(self) -> dict[str, dict]:
        """
        获取任务链的状态字典

        :return: 任务链状态字典
        """
        return self.status_dict

    def get_graph_summary(self) -> dict:
        """获取任务链的摘要信息字典"""
        return self.graph_summary

    def get_stage_history(self) -> dict[str, list[dict]]:
        """获取任务链的历史状态信息字典"""
        return self.stage_history

    def get_graph_analysis(self) -> dict:
        """
        获取任务图的分析信息
        """
        return {
            "isDAG": self.isDAG,
            "schedule_mode": self.schedule_mode,
            "class_name": self.__class__.__name__,
            "layers_dict": self.layers_dict,
        }

    def get_structure_json(self) -> list[dict]:
        """
        获取任务图的 JSON 结构
        """
        return self.structure_json

    def get_structure_list(self) -> list[str]:
        """
        获取任务图的结构列表
        """
        return self.structure_list

    def get_networkx_graph(self):  # returns nx.DiGraph
        """
        获取任务图的 networkx 有向图（DiGraph）
        """
        return self.networkx_graph

    def get_fallback_path(self) -> str:
        """
        获取失败任务的回退路径
        """
        if self.fail_listener.jsonl_path is None:
            return ""
        return str(Path(self.fail_listener.jsonl_path).resolve())

    def get_stage_input_trace(self, stage_tag: str) -> str:
        """
        获取任务节点的输入依赖关系树
        """
        if not self._use_ctree:
            return ""

        input_ids: set = self.input_ids[stage_tag]
        descendants = self.ctree_client.descendants_batch(list(input_ids), "meta")
        return format_descendants_forest(descendants, STAGE_STYLE)

    def get_error_trace(self, error_id: int) -> str:
        """
        获取错误任务的依赖关系树
        """
        provenance = self.ctree_client.provenance(error_id)
        return format_provenance_forest(provenance, STAGE_STYLE)
