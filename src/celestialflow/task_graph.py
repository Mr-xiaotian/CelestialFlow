import time, os
import warnings
import multiprocessing
from collections.abc import Iterable
from collections import defaultdict, deque
from datetime import datetime
from multiprocessing import Queue as MPQueue
from typing import Any, Dict, List

from celestialtree import (
    Client as CelestialTreeClient,
    NullClient as NullCelestialTreeClient,
    format_descendants_forest,
    format_provenance_forest,
)

from . import task_tools
from .task_stage import TaskStage
from .task_report import TaskReporter, NullTaskReporter
from .task_logger import LogListener, TaskLogger
from .task_queue import TaskQueue
from .task_types import (
    TaskEnvelope,
    StageStatus,
    UnconsumedError,
    TerminationSignal,
    STAGE_STYLE,
)


class TaskGraph:
    def __init__(
        self,
        root_stages: List[TaskStage],
        schedule_mode: str = "eager",
        log_level: str = "SUCCESS",
    ):
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
        self.init_structure_graph()
        self.analyze_graph()
        self.set_schedule_mode(schedule_mode)

    def init_env(self):
        """
        初始化环境
        """
        self.processes: List[multiprocessing.Process] = []

        self.init_state()
        self.init_logger()
        self.init_resources()

    def init_state(self):
        """
        初始化状态
        """
        self.stage_runtime_dict: Dict[str, dict] = defaultdict(
            dict
        )  # 用于保存每个节点的运行信息
        self.status_dict: Dict[str, dict] = defaultdict(
            dict
        )  # 用于保存每个节点的上一次collect_runtime_snapshot()的状态信息
        self.graph_summary: Dict[str, int | float] = {}
        self.input_ids: Dict[str, set] = defaultdict(set)

        self.total_error_num = 0

    def init_resources(self):
        """
        初始化每个阶段资源
        """
        self.fail_queue = MPQueue()

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
            stage.reset_counter()

            # 记录节点
            stage_runtime["stage"] = stage

            stage_runtime["in_queue"] = TaskQueue(
                queue_list=[],
                queue_tags=[],
                direction="in",
                stage=stage,
                task_logger=self.task_logger,
                ctree_client=None,
            )
            stage_runtime["out_queue"] = TaskQueue(
                queue_list=[],
                queue_tags=[],
                direction="out",
                stage=stage,
                task_logger=self.task_logger,
                ctree_client=None,
            )

            visited_stages.add(stage_tag)
            queue.extend(stage.next_stages)

        for stage_tag, stage_runtime in self.stage_runtime_dict.items():
            stage: TaskStage = stage_runtime["stage"]
            in_queue: TaskQueue = stage_runtime["in_queue"]

            # 遍历每个前驱，创建边队列
            for prev_stage in stage.prev_stages:
                prev_stage_tag = prev_stage.get_tag() if prev_stage else None
                q = MPQueue()

                # sink side
                in_queue.add_queue(q, prev_stage_tag)

                # source side
                if prev_stage is not None:
                    self.stage_runtime_dict[prev_stage_tag]["out_queue"].add_queue(
                        q, stage_tag
                    )

    def init_logger(self):
        """
        初始化日志
        """
        self.log_listener = LogListener()
        self.task_logger = TaskLogger(self.log_listener.get_queue(), self.log_level)

    def init_structure_graph(self):
        """
        初始化任务图结构
        """
        self.structure_json = task_tools.build_structure_graph(self.root_stages)

    def set_root_stages(self, root_stages: List[TaskStage]):
        """
        设置根节点

        :param root_stages: 根节点列表
        """
        self.root_stages = root_stages
        for stage in root_stages:
            if not stage.prev_stages:
                stage.add_prev_stages(None)

    def set_schedule_mode(self, schedule_mode: str):
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

    def set_reporter(self, is_report=False, host="127.0.0.1", port=5000):
        """
        设定报告器

        :param is_report: 是否启用报告器
        :param host: 报告器主机地址
        :param port: 报告器端口
        """
        if is_report:
            self.reporter = TaskReporter(
                host=host,
                port=port,
                task_graph=self,
                task_logger=self.task_logger,
            )
        else:
            self.reporter = NullTaskReporter()

    def set_ctree(
        self, use_ctree=False, host="127.0.0.1", http_port=7777, grpc_port=7778
    ):
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

        if use_ctree:
            self.ctree_client = CelestialTreeClient(
                host=host, http_port=http_port, grpc_port=grpc_port, transport="grpc"
            )
            if not self.ctree_client.health():
                raise Exception("CelestialTreeClient is not available")
        else:
            self.ctree_client = NullCelestialTreeClient()

    def set_log_level(self, level="SUCCESS"):
        """
        设置日志级别

        :param level: 日志级别, 默认为 "SUCCESS"
        """
        self.log_level = level.upper()

    def set_graph_mode(self, stage_mode: str, execution_mode: str):
        """
        设置任务链的执行模式

        :param stage_mode: 节点执行模式, 可选值为 'serial' 或 'process'
        :param execution_mode: 节点内部执行模式, 可选值为 'serial' 或 'thread''
        """

        def set_subsequent_stage_mode(stage: TaskStage):
            stage.set_stage_mode(stage_mode)
            stage.set_execution_mode(execution_mode)
            visited_stages.add(stage)

            for next_stage in stage.next_stages:
                if next_stage in visited_stages:
                    continue
                set_subsequent_stage_mode(next_stage)

        visited_stages = set()
        for root_stage in self.root_stages:
            set_subsequent_stage_mode(root_stage)
        self.init_structure_graph()

    def put_stage_queue(self, tasks_dict: dict, put_termination_signal=True):
        """
        将任务放入队列

        :param tasks_dict: 待处理的任务字典
        :param put_termination_signal: 是否放入终止信号
        """
        for tag, tasks in tasks_dict.items():
            stage: TaskStage = self.stage_runtime_dict[tag]["stage"]
            in_queue: TaskQueue = self.stage_runtime_dict[tag]["in_queue"]
            input_ids: set = self.input_ids[tag]

            for task in tasks:
                if isinstance(task, TerminationSignal):
                    termination_id = self.ctree_client.emit(
                        "termination.input",
                        payload=stage.get_summary(),
                    )
                    in_queue.put(TerminationSignal(termination_id))
                    continue

                input_id = self.ctree_client.emit(
                    "task.input",
                    payload=stage.get_summary(),
                )
                envelope = TaskEnvelope.wrap(task, input_id)
                in_queue.put_first(envelope)
                input_ids.add(input_id)

                stage.task_counter.add_init_value(1)
                self.task_logger.task_input(
                    stage.get_func_name(),
                    stage.get_task_repr(task),
                    stage.get_tag(),
                    input_id,
                )

        if put_termination_signal:
            for root_stage in self.root_stages:
                root_stage_tag = root_stage.get_tag()
                root_in_queue: TaskQueue = self.stage_runtime_dict[root_stage_tag][
                    "in_queue"
                ]

                termination_id = self.ctree_client.emit(
                    "termination.input",
                    payload=root_stage.get_summary(),
                )
                root_in_queue.put(TerminationSignal(termination_id))

    def start_graph(self, init_tasks_dict: dict, put_termination_signal: bool = True):
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
            self.log_listener.start()
            self.start_time = time.time()
            self.task_logger.start_graph(self.get_structure_list())
            self._persist_structure_metadata()
            self.reporter.start()

            self.put_stage_queue(init_tasks_dict, put_termination_signal)
            self._excute_stages()

        finally:
            self.finalize_nodes()

            self.reporter.stop()
            self.release_resources()
            self.task_logger.end_graph(time.time() - self.start_time)
            self.log_listener.stop()

    def _excute_stages(self):
        """
        执行所有节点
        """
        if self.schedule_mode == "eager":
            # eager schedule_mode：一次性执行所有节点
            for stage_runtime in self.stage_runtime_dict.values():
                self._execute_stage(stage_runtime["stage"])

            for p in self.processes:
                p.join()
                self.task_logger.process_exit(p.name, p.exitcode)
        else:
            # staged schedule_mode：一层层地顺序执行
            for layer_level, layer in self.layers_dict.items():
                self.task_logger.start_layer(layer, layer_level)
                start_time = time.time()

                processes = []
                for stage_tag in layer:
                    stage: TaskStage = self.stage_runtime_dict[stage_tag]["stage"]
                    self._execute_stage(stage)
                    if stage.stage_mode == "process":
                        processes.append(self.processes[-1])  # 最新的进程

                # join 当前层的所有进程（如果有）
                for p in processes:
                    p.join()
                    self.task_logger.process_exit(p.name, p.exitcode)

                self.task_logger.end_layer(layer, time.time() - start_time)

    def _execute_stage(self, stage: TaskStage):
        """
        执行单个节点

        :param stage: 节点
        """
        stage_tag = stage.get_tag()
        stage_runtime = self.stage_runtime_dict[stage_tag]

        log_queue = self.log_listener.get_queue()

        # 输入输出队列
        input_queues: TaskQueue = stage_runtime["in_queue"]
        output_queues: TaskQueue = stage_runtime["out_queue"]

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
                args=(input_queues, output_queues, self.fail_queue, log_queue),
                name=stage_tag,
            )
            p.start()
            self.processes.append(p)
        else:
            stage.start_stage(input_queues, output_queues, self.fail_queue, log_queue)

    def finalize_nodes(self):
        """
        确保所有子进程安全结束，更新节点状态，并导出每个节点队列剩余任务。
        """
        # 确保所有进程安全结束（不一定要 terminate，但如果没结束就强制）
        for p in self.processes:
            if p.is_alive():
                self.task_logger.process_termination_attempt(p.name)
                p.terminate()
                p.join(timeout=5)
                if p.is_alive():
                    self.task_logger.process_termination_timeout(p.name)
                self.task_logger.process_exit(p.name, p.exitcode)

        # 更新所有节点状态为“已停止”
        for stage_runtime in self.stage_runtime_dict.values():
            stage: TaskStage = stage_runtime["stage"]
            stage.mark_stopped()

        # 收集并持久化每个 stage 中未消费的任务
        for stage_tag, stage_runtime in self.stage_runtime_dict.items():
            stage: TaskStage = stage_runtime["stage"]
            in_queue: TaskQueue = stage_runtime["in_queue"]

            remaining_sources = in_queue.drain()
            stage.error_counter.value += len(remaining_sources)

            # 持久化逻辑
            for source in remaining_sources:
                task = source.task
                task_id = source.id
                error_id = self.ctree_client.emit(
                    "task.error",
                    [task_id],
                    payload=stage.get_summary(),
                )

                self.fail_queue.put(
                    {
                        "ts": time.time(),
                        "stage_tag": stage_tag,
                        "error_message": "UnconsumedError()",
                        "error_id": error_id,
                        "task": str(task),
                    }
                )
                self.task_logger.task_error(
                    stage.get_func_name(),
                    stage.get_task_repr(task),
                    UnconsumedError(),
                    task_id,
                    error_id,
                )

    def release_resources(self):
        """
        释放资源
        """
        for stage_runtime in self.stage_runtime_dict.values():
            stage: TaskStage = stage_runtime["stage"]
            stage.release_queue()

        self.handle_fail_queue()
        task_tools.cleanup_mpqueue(self.fail_queue)

    def handle_fail_queue(self):
        """
        消费 fail_queue, 存储错误数据到fallback
        """
        failures = []
        while True:
            try:
                item: dict = self.fail_queue.get_nowait()
            except Exception as e:
                break

            ts = item["ts"]
            stage_tag = item["stage_tag"]
            error_message = item["error_message"]
            error_id = item["error_id"]
            task_str = item["task"]

            failures.append((ts, stage_tag, error_message, error_id, task_str))
            self.total_error_num += 1

        self._persist_failures(failures)

    def collect_runtime_snapshot(self):
        """
        收集运行时快照
        """
        status_dict = {}
        now = time.time()
        interval = self.reporter.interval

        totals = {
            "total_successed": 0,
            "total_pending": 0,
            "total_failed": 0,
            "total_duplicated": 0,
            "total_nodes": 0,  # running nodes
            "total_remain": 0.0,
        }

        # 为全局预计 remaining 收集
        running_elapsed_map: Dict[str, float] = {}
        running_processed_map: Dict[str, int] = {}
        running_pending_map: Dict[str, int] = {}
        running_remaining_map: Dict[str, float] = {}

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
            elapsed = task_tools.calc_elapsed(
                status, start_time, last_elapsed, last_pending, interval
            )

            # 估算剩余时间
            remaining = task_tools.calc_remaining(
                stage_counts["tasks_processed"], stage_counts["tasks_pending"], elapsed
            )

            if status == StageStatus.RUNNING:
                totals["total_nodes"] += 1

            running_processed_map[stage_tag] = int(stage_counts["tasks_processed"] or 0)
            running_pending_map[stage_tag] = int(stage_counts["tasks_pending"] or 0)
            running_elapsed_map[stage_tag] = float(elapsed or 0.0)
            running_remaining_map[stage_tag] = float(remaining or 0.0)

            # 计算平均时间（秒/任务）并格式化为字符串
            avg_time_str = task_tools.format_avg_time(
                elapsed, stage_counts["tasks_processed"]
            )

            history: list = list(last_stage_status_dict.get("history", []))
            history.append(
                {
                    "timestamp": now,
                    "tasks_processed": stage_counts["tasks_processed"],
                }
            )
            history.pop(0) if len(history) > 20 else None

            status_dict[stage_tag] = {
                **stage.get_summary(),
                "status": status,
                **stage_counts,
                **deltas,
                "start_time": start_time,
                "elapsed_time": elapsed,
                "remaining_time": remaining,
                "task_avg_time": avg_time_str,
                "history": list(history),
            }

        if not self.isDAG:
            totals["total_remain"] = max(running_remaining_map.values(), default=0.0)
        else:
            G = self.get_networkx_graph()
            expected_pending_map = task_tools.calc_global_remain_equal_pred(
                G, running_processed_map, running_pending_map, running_elapsed_map
            )
            totals["total_remain"] = max(expected_pending_map.values(), default=0.0)

        self.status_dict = status_dict
        self.graph_summary = dict(totals)

    def _persist_structure_metadata(self):
        """
        在运行开始时写入任务结构元信息到 jsonl 文件
        """
        date_str = datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d")
        time_str = datetime.fromtimestamp(self.start_time).strftime("%H-%M-%S-%f")[:-3]
        self.error_jsonl_path = f"./fallback/{date_str}/graph_errors({time_str}).jsonl"

        log_item = {
            "timestamp": datetime.now().isoformat(),
            "structure": self.get_structure_json(),
        }
        task_tools.append_jsonl_log(log_item, self.error_jsonl_path, self.task_logger)

    def _persist_failures(self, failures: Iterable[tuple]):
        """
        批量写入多条错误日志到 jsonl 文件中

        :param failures: 错误日志列表(错误时间戳, 阶段标签, 错误信息, 任务字符串)
        """
        if not failures:
            return

        log_items = (
            {
                "timestamp": datetime.fromtimestamp(ts).isoformat(),
                "stage": stage_tag,
                "error_repr": task_tools.format_repr(err, 100),
                "task_repr": task_tools.format_repr(task, 100),
                "error": err,
                "task": task,
                "error_id": err_id,
                "ts": ts,
            }
            for ts, stage_tag, err, err_id, task in failures
        )
        task_tools.append_jsonl_logs(log_items, self.error_jsonl_path, self.task_logger)

    def get_fail_by_stage_dict(self):
        return task_tools.load_task_by_stage(self.error_jsonl_path)

    def get_fail_by_error_dict(self):
        return task_tools.load_task_by_error(self.error_jsonl_path)

    def get_status_dict(self) -> Dict[str, dict]:
        """
        获取任务链的状态字典

        :return: 任务链状态字典
        """
        return self.status_dict

    def get_graph_summary(self) -> dict:
        return self.graph_summary

    def get_graph_topology(self) -> dict:
        """
        获取任务图的拓扑信息
        """
        return {
            "isDAG": self.isDAG,
            "schedule_mode": self.schedule_mode,
            "class_name": self.__class__.__name__,
            "layers_dict": self.layers_dict,
        }

    def get_structure_json(self) -> List[dict]:
        return self.structure_json

    def get_structure_list(self) -> List[str]:
        return task_tools.format_structure_list_from_graph(self.structure_json)

    def get_networkx_graph(self):
        return task_tools.format_networkx_graph(self.structure_json)

    def get_error_jsonl_path(self) -> str:
        return os.path.abspath(self.error_jsonl_path)

    def get_stage_input_trace(self, stage_tag: str) -> str:
        if not self._use_ctree:
            return ""

        input_ids: set = self.input_ids[stage_tag]
        descendants = self.ctree_client.descendants_batch(list(input_ids), "meta")
        return format_descendants_forest(descendants, STAGE_STYLE)

    def get_error_trace(self, error_id):
        provenance = self.ctree_client.provenance(error_id)
        return format_provenance_forest(provenance, STAGE_STYLE)

    def analyze_graph(self):
        """
        分析任务图，计算 DAG 属性和层级信息
        """
        networkx_graph = self.get_networkx_graph()
        self.layers_dict = {}

        self.isDAG = task_tools.is_directed_acyclic_graph(networkx_graph)
        if self.isDAG:
            stage_level_dict = task_tools.compute_node_levels(networkx_graph)
            self.layers_dict = task_tools.cluster_by_value_sorted(stage_level_dict)

    def test_methods(
        self,
        init_tasks_dict: Dict[str, List],
        stage_modes: list = None,
        execution_modes: list = None,
    ) -> Dict[str, Any]:
        """
        测试 TaskGraph 在 'serial' 和 'process' 模式下的执行时间。

        :param init_tasks_dict: 初始化任务字典
        :param stage_modes: 阶段模式列表，默认为 ['serial', 'process']
        :param execution_modes: 执行模式列表，默认为 ['serial', 'thread']
        :return: 包含两种执行模式下的执行时间的字典
        """
        results = {}
        test_table_list = []
        fail_by_error_dict = {}
        fail_by_stage_dict = {}

        stage_modes = stage_modes or ["serial", "process"]
        execution_modes = execution_modes or ["serial", "thread"]
        for stage_mode in stage_modes:
            time_list = []
            for execution_mode in execution_modes:
                start_time = time.time()
                self.init_env()
                self.set_graph_mode(stage_mode, execution_mode)
                self.start_graph(init_tasks_dict)
                fail_by_stage_dict.update(self.get_fail_by_stage_dict())
                fail_by_error_dict.update(self.get_fail_by_error_dict())

                time_list.append(time.time() - start_time)

            test_table_list.append(time_list)

        results["Time table"] = (
            test_table_list,
            stage_modes,
            execution_modes,
            r"stage\execution",
        )
        results["Fail stage dict"] = fail_by_stage_dict
        results["Fail error dict"] = fail_by_error_dict
        return results
