import time
import multiprocessing
from collections.abc import Iterable
from collections import defaultdict, deque
from datetime import datetime
from multiprocessing import Queue as MPQueue
from typing import Any, Dict, List

from .task_stage import TaskStage
from .task_report import TaskReporter, NullTaskReporter
from .task_logging import LogListener, TaskLogger
from .task_queue import TaskQueue
from .task_types import TaskEnvelope, StageStatus, TerminationSignal, TERMINATION_SIGNAL
from .task_tools import (
    format_duration,
    format_timestamp,
    cleanup_mpqueue,
    build_structure_graph,
    format_structure_list_from_graph,
    append_jsonl_log,
    append_jsonl_logs,
    format_networkx_graph,
    is_directed_acyclic_graph,
    compute_node_levels,
    cluster_by_value_sorted,
    load_task_by_stage,
    load_task_by_error,
    format_repr,
)
from .adapters.celestialtree import (
    Client as CelestialTreeClient,
    NullClient as NullCelestialTreeClient,
)


class TaskGraph:
    def __init__(self, root_stages: List[TaskStage], layout_mode: str = "process"):
        """
        初始化 TaskGraph 实例。

        TaskGraph 表示一组 TaskStage 节点所构成的任务图，可用于构建并行、串行、
        分层等多种形式的任务执行流程。通过分析图结构和调度布局策略，实现灵活的
        DAG 任务调度控制。

        :param root_stages : List[TaskStage]
            根节点 TaskStage 列表，用于构建任务图的入口节点。
            支持多根节点（森林结构），系统将自动构建整个任务依赖图。

        :param layout_mode : str, optional, default = 'process'
            控制任务图的调度布局模式，支持以下两种策略：
            - 'process'：
                默认模式。所有节点一次性调度并发执行，依赖关系通过队列流自动控制。
                适用于最大化并行度的执行场景。
            - 'serial'：
                分层执行模式。任务图必须为有向无环图（DAG）。
                节点按层级顺序逐层启动，确保上层所有任务完成后再启动下一层。
                更利于调试、性能分析和阶段性资源控制。

        :return ValueError
            如果输入图不合法或 layout_mode 参数错误。
        """
        self.set_root_stages(root_stages)

        self.init_env()
        self.init_structure_graph()
        self.analyze_graph()
        self.set_layout_mode(layout_mode)
        self.set_reporter()
        self.set_ctree()

    def init_env(self):
        """
        初始化环境
        """
        self.processes: List[multiprocessing.Process] = []

        self.init_dict()
        self.init_log()
        self.init_resources()

    def init_dict(self):
        """
        初始化字典
        """
        self.stages_status_dict: Dict[str, dict] = defaultdict(
            dict
        )  # 用于保存每个节点的状态信息
        self.last_status_dict: Dict[str, dict] = defaultdict(
            dict
        )  # 用于保存每个节点的上一次状态信息

        self.error_data: List[dict] = []

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

            # 刷新所有 counter
            stage.reset_counter()

            # 记录节点
            self.stages_status_dict[stage_tag]["stage"] = stage
            self.stages_status_dict[stage_tag]["in_queue"] = TaskQueue(
                queue_list=[],
                queue_tag=[],
                logger_queue=self.log_listener.get_queue(),
                stage_tag=stage_tag,
                direction="in",
            )

            self.stages_status_dict[stage_tag]["out_queue"] = TaskQueue(
                queue_list=[],
                queue_tag=[],
                logger_queue=self.log_listener.get_queue(),
                stage_tag=stage_tag,
                direction="out",
            )
            visited_stages.add(stage_tag)

            queue.extend(stage.next_stages)

        for stage_tag in self.stages_status_dict:
            stage: TaskStage = self.stages_status_dict[stage_tag]["stage"]
            in_queue: TaskQueue = self.stages_status_dict[stage_tag]["in_queue"]

            # 遍历每个前驱，创建边队列
            for prev_stage in stage.prev_stages:
                prev_stage_tag = prev_stage.get_tag() if prev_stage else None
                q = MPQueue()

                # sink side
                in_queue.add_queue(q, prev_stage_tag)

                # source side
                if prev_stage is not None:
                    self.stages_status_dict[prev_stage_tag]["out_queue"].add_queue(
                        q, stage_tag
                    )

    def init_log(self, level="INFO"):
        """
        初始化日志

        :param level: 日志级别, 默认为 "INFO"
        """
        self.log_listener = LogListener(level)
        self.task_logger = TaskLogger(self.log_listener.get_queue())

    def init_structure_graph(self):
        """
        初始化任务图结构
        """
        self.structure_json = build_structure_graph(self.root_stages)

    def set_root_stages(self, root_stages: List[TaskStage]):
        """
        设置根节点

        :param root_stages: 根节点列表
        """
        self.root_stages = root_stages
        for stage in root_stages:
            if not stage.prev_stages:
                stage.add_prev_stages(None)

    def set_layout_mode(self, layout_mode: str):
        """
        设置任务链的执行模式

        :param layout_mode: 节点执行模式, 可选值为 'serial' 或 'process'
        """
        if layout_mode == "serial" and self.isDAG:
            self.layout_mode = "serial"
        else:
            self.layout_mode = "process"

    def set_reporter(self, is_report=False, host="127.0.0.1", port=5000):
        """
        设定报告器

        :param is_report: 是否启用报告器
        :param host: 报告器主机地址
        :param port: 报告器端口
        """
        if is_report:
            self.reporter = TaskReporter(
                self, self.log_listener.get_queue(), host, port
            )
        else:
            self.reporter = NullTaskReporter()

    def set_ctree(self, use_ctree=False, host="127.0.0.1", port=7777):
        """
        设定事件树客户端

        :param use_ctree: 是否使用事件树
        :param host: 事件树主机地址
        :param port: 事件树端口
        """
        self._use_ctree = use_ctree
        self._ctree_host = host
        self._ctree_port = port

        if use_ctree:
            self.ctree_client = CelestialTreeClient(host=host, port=port)
            if not self.ctree_client.health():
                self._use_ctree = False
                self.ctree_client = NullCelestialTreeClient()
        else:
            self.ctree_client = NullCelestialTreeClient()

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
            stage: TaskStage = self.stages_status_dict[tag]["stage"]
            in_queue: TaskQueue = self.stages_status_dict[tag]["in_queue"]

            for task in tasks:
                if isinstance(task, TerminationSignal):
                    in_queue.put(TERMINATION_SIGNAL)
                    continue

                input_id = self.ctree_client.emit(
                    "task.input", message=f"In '{stage.get_tag()}'"
                )
                envelope = TaskEnvelope.wrap(task, input_id)
                in_queue.put_first(envelope)
                stage.task_counter.add_init_value(1)
                self.task_logger.task_input(
                    stage.get_func_name(),
                    stage.get_task_info(task),
                    stage.get_tag(),
                    input_id,
                )

        if put_termination_signal:
            for root_stage in self.root_stages:
                root_stage_tag = root_stage.get_tag()
                root_in_queue: TaskQueue = self.stages_status_dict[root_stage_tag][
                    "in_queue"
                ]
                root_in_queue.put(TERMINATION_SIGNAL)

    def start_graph(self, init_tasks_dict: dict, put_termination_signal: bool = True):
        """
        启动任务链

        :param init_tasks_dict: 任务列表
        :param put_termination_signal: 是否注入终止信号
        """
        try:
            self.log_listener.start()
            self.start_time = time.time()
            self.task_logger.start_graph(self.get_structure_list())
            self._persist_structure_metadata()
            self.reporter.start()

            self.put_stage_queue(init_tasks_dict, put_termination_signal)
            self._excute_stages()

        finally:
            self.reporter.stop()
            self.handle_fail_queue()
            self.finalize_nodes()
            self.release_resources()

            self.task_logger.end_graph(time.time() - self.start_time)
            self.log_listener.stop()

    def _excute_stages(self):
        """
        执行所有节点
        """
        if self.layout_mode == "process":
            # 默认逻辑：一次性执行所有节点
            for tag in self.stages_status_dict:
                self._execute_stage(self.stages_status_dict[tag]["stage"])

            for p in self.processes:
                p.join()
                self.stages_status_dict[p.name]["status"] = StageStatus.STOPPED
                self.task_logger._log("DEBUG", f"{p.name} exitcode: {p.exitcode}")
        else:
            # serial layout_mode：一层层地顺序执行
            for layer_level, layer in self.layers_dict.items():
                self.task_logger.start_layer(layer, layer_level)
                start_time = time.time()

                processes = []
                for stage_tag in layer:
                    stage: TaskStage = self.stages_status_dict[stage_tag]["stage"]
                    self._execute_stage(stage)
                    if stage.stage_mode == "process":
                        processes.append(self.processes[-1])  # 最新的进程

                # join 当前层的所有进程（如果有）
                for p in processes:
                    p.join()
                    self.stages_status_dict[p.name]["status"] = StageStatus.STOPPED
                    self.task_logger._log("DEBUG", f"{p.name} exitcode: {p.exitcode}")

                self.task_logger.end_layer(layer, time.time() - start_time)

    def _execute_stage(self, stage: TaskStage):
        """
        执行单个节点

        :param stage: 节点
        """
        stage_tag = stage.get_tag()

        logger_queue = self.log_listener.get_queue()

        # 输入输出队列
        input_queues = self.stages_status_dict[stage_tag]["in_queue"]
        output_queues = self.stages_status_dict[stage_tag]["out_queue"]

        self.stages_status_dict[stage_tag]["status"] = StageStatus.RUNNING
        self.stages_status_dict[stage_tag]["start_time"] = time.time()

        if self._use_ctree:
            stage.set_ctree(self._ctree_host, self._ctree_port)
        else:
            stage.set_nullctree(self.ctree_client.event_id)

        if stage.stage_mode == "process":
            p = multiprocessing.Process(
                target=stage.start_stage,
                args=(input_queues, output_queues, self.fail_queue, logger_queue),
                name=stage_tag,
            )
            p.start()
            self.processes.append(p)
        else:
            stage.start_stage(
                input_queues, output_queues, self.fail_queue, logger_queue
            )
            self.stages_status_dict[stage_tag]["status"] = StageStatus.STOPPED

    def finalize_nodes(self):
        """
        确保所有子进程安全结束，更新节点状态，并导出每个节点队列剩余任务。
        """
        # 确保所有进程安全结束（不一定要 terminate，但如果没结束就强制）
        for p in self.processes:
            if p.is_alive():
                self.task_logger._log(
                    "WARNING", f"检测到进程 {p.name} 仍在运行, 尝试终止"
                )
                p.terminate()
                p.join(timeout=5)
                if p.is_alive():
                    self.task_logger._log("WARNING", f"进程 {p.name} 仍未完全退出")
                self.task_logger._log("DEBUG", f"{p.name} exitcode: {p.exitcode}")

        # 更新所有节点状态为“已停止”
        for stage_tag, stage_status in self.stages_status_dict.items():
            stage_status["status"] = StageStatus.STOPPED  # 已停止

        # 收集并持久化每个 stage 中未消费的任务
        failures = []
        for stage_tag, stage_status in self.stages_status_dict.items():
            in_queue: TaskQueue = stage_status["in_queue"]
            remaining_sources = in_queue.drain()

            if not remaining_sources:
                continue

            # 持久化逻辑
            ts = time.time()
            failures.extend([(ts, stage_tag, "UnconsumedError", str(source.task)) for source in remaining_sources])
        self._persist_failures(failures)

    def release_resources(self):
        """
        释放资源
        """
        for stage_status_dict in self.stages_status_dict.values():
            stage_status_dict["stage"].release_queue()

        cleanup_mpqueue(self.fail_queue)

    def handle_fail_queue(self):
        """
        消费 fail_queue, 构建失败字典
        """
        failures = []
        while True:
            try:
                item: dict = self.fail_queue.get_nowait()
            except Exception:
                break
            
            timestamp = item["timestamp"]
            stage_tag = item["stage_tag"]
            error_info = item["error_info"]
            task_str = item["task"]

            self.error_data.append(
                {
                    "timestamp": timestamp,
                    "node": stage_tag,
                    "error": error_info,
                    "task_repr": format_repr(task_str, 100),
                }
            )
            failures.append((timestamp, stage_tag, error_info, task_str))
        self._persist_failures(failures)

    def _persist_structure_metadata(self):
        """
        在运行开始时写入任务结构元信息到 jsonl 文件
        """
        date_str = datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d")
        time_str = datetime.fromtimestamp(self.start_time).strftime("%H-%M-%S-%f")[:-3]
        self.error_jsonl_path = (
            f"./fallback/{date_str}/graph_errors({time_str}).jsonl"
        )

        log_item = {
            "timestamp": datetime.now().isoformat(),
            "structure": self.get_structure_json(),
        }
        append_jsonl_log(log_item, self.error_jsonl_path, self.task_logger)

    def _persist_failures(self, failures: Iterable[tuple]):
        """
        批量写入多条错误日志到 jsonl 文件中

        :param failures: 错误日志列表(错误时间戳, 阶段标签, 错误信息, 任务字符串)
        """
        log_items = (
            {
                "timestamp": datetime.fromtimestamp(ts).isoformat(),
                "stage": stage,
                "error": err,
                "task": task,
            }
            for ts, stage, err, task in failures
        )
        append_jsonl_logs(log_items, self.error_jsonl_path, self.task_logger)

    def get_error_data(self):
        """
        返回错误数据
        """
        return self.error_data

    def get_fail_by_stage_dict(self):
        return load_task_by_stage(self.error_jsonl_path)

    def get_fail_by_error_dict(self):
        return load_task_by_error(self.error_jsonl_path)

    def get_status_dict(self) -> Dict[str, dict]:
        """
        获取任务链的状态字典

        :return: 任务链状态字典
        """
        status_dict = {}
        now = time.time()
        interval = self.reporter.interval

        for tag, stage_status_dict in self.stages_status_dict.items():
            stage: TaskStage = stage_status_dict["stage"]
            last_stage_status_dict: dict = self.last_status_dict.get(tag, {})

            status = stage_status_dict.get("status", StageStatus.NOT_STARTED)

            input = stage.task_counter.value
            successed = stage.success_counter.value
            failed = stage.error_counter.value
            duplicated = stage.duplicate_counter.value
            processed = successed + failed + duplicated
            pending = max(0, input - processed)

            add_successed = successed - last_stage_status_dict.get("tasks_successed", 0)
            add_failed = failed - last_stage_status_dict.get("tasks_failed", 0)
            add_duplicated = duplicated - last_stage_status_dict.get(
                "tasks_duplicated", 0
            )
            add_processed = processed - last_stage_status_dict.get("tasks_processed", 0)
            add_pending = pending - last_stage_status_dict.get("tasks_pending", 0)

            start_time = stage_status_dict.get("start_time", 0)
            # 更新时间消耗（仅在 pending 非 0 时刷新）
            if start_time:
                elapsed = stage_status_dict.get("elapsed_time", 0)
                # 如果上一次是 pending，则累计时间
                if last_stage_status_dict.get("tasks_pending", 0):
                    # 如果上一次活跃, 那么无论当前状况，累计一次更新时间
                    elapsed += interval
            else:
                elapsed = 0

            stage_status_dict["elapsed_time"] = elapsed

            # 估算剩余时间
            remaining = (pending / processed * elapsed) if processed and pending else 0

            # 计算平均时间（秒/任务）并格式化为字符串
            if processed:
                avg_time = elapsed / processed
                if avg_time >= 1.0:
                    # 显示 "X.XX s/it"
                    avg_time_str = f"{avg_time:.2f}s/it"
                else:
                    # 显示 "X.XX it/s"（取倒数）
                    its_per_sec = processed / elapsed if elapsed else 0
                    avg_time_str = f"{its_per_sec:.2f}it/s"
            else:
                avg_time_str = "N/A"  # 或 "0.00s/it"

            history: list = stage_status_dict.get("history", [])
            history.append(
                {
                    "timestamp": now,
                    "tasks_processed": processed,
                }
            )
            history.pop(0) if len(history) > 20 else None
            stage_status_dict["history"] = history

            status_dict[tag] = {
                **stage.get_stage_summary(),
                "status": status,
                "tasks_successed": successed,
                "tasks_failed": failed,
                "tasks_duplicated": duplicated,
                "tasks_processed": processed,
                "tasks_pending": pending,
                "add_tasks_successed": add_successed,
                "add_tasks_failed": add_failed,
                "add_tasks_duplicated": add_duplicated,
                "add_tasks_processed": add_processed,
                "add_tasks_pending": add_pending,
                "start_time": format_timestamp(start_time),
                "elapsed_time": format_duration(elapsed),
                "remaining_time": format_duration(remaining),
                "task_avg_time": avg_time_str,
                "history": history,
            }

        self.last_status_dict = status_dict

        return status_dict

    def get_graph_topology(self):
        """
        获取任务图的拓扑信息
        """
        return {
            "isDAG": self.isDAG,
            "layout_mode": self.layout_mode,
            "class_name": self.__class__.__name__,
            "layers_dict": self.layers_dict,
        }

    def get_structure_json(self):
        return self.structure_json

    def get_structure_list(self):
        return format_structure_list_from_graph(self.structure_json)

    def get_networkx_graph(self):
        return format_networkx_graph(self.structure_json)

    def analyze_graph(self):
        """
        分析任务图，计算 DAG 属性和层级信息
        """
        networkx_graph = self.get_networkx_graph()
        self.layers_dict = {}

        self.isDAG = is_directed_acyclic_graph(networkx_graph)
        if self.isDAG:
            stage_level_dict = compute_node_levels(networkx_graph)
            self.layers_dict = cluster_by_value_sorted(stage_level_dict)

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
