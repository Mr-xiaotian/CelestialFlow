import time
import multiprocessing
from collections import defaultdict, deque
from datetime import datetime
from multiprocessing import Value as MPValue, Lock as MPLock
from multiprocessing import Queue as MPQueue
from typing import Any, Dict, List, Tuple

from .task_manage import TaskManager
from .task_nodes import TaskSplitter
from .task_support import TERMINATION_SIGNAL, TaskError, TaskReporter, LogListener, TaskLogger, ValueWrapper, TerminationSignal, StageStatus
from .task_tools import (
    format_duration,
    format_timestamp,
    cleanup_mpqueue,
    make_hashable,
    build_structure_graph,
    format_structure_list_from_graph,
    append_jsonl_log,
    format_networkx_graph,
    is_directed_acyclic_graph,
    compute_node_levels,
    cluster_by_value_sorted,
)


class TaskGraph:
    def __init__(self, root_stages: List[TaskManager], layout_mode: str = "process"):
        """
        初始化 TaskGraph 实例。

        TaskGraph 表示一组 TaskManager 节点所构成的任务图，可用于构建并行、串行、
        分层等多种形式的任务执行流程。通过分析图结构和调度布局策略，实现灵活的
        DAG 任务调度控制。

        Parameters
        ----------
        root_stages : List[TaskManager]
            根节点 TaskManager 列表，用于构建任务图的入口节点。
            支持多根节点（森林结构），系统将自动构建整个任务依赖图。

        layout_mode : str, optional, default = 'process'
            控制任务图的调度布局模式，支持以下两种策略：
            
            - 'process'：
                默认模式。所有节点一次性调度并发执行，依赖关系通过队列流自动控制。
                适用于最大化并行度的执行场景。
            
            - 'serial'：
                分层执行模式。任务图必须为有向无环图（DAG）。
                节点按层级顺序逐层启动，确保上层所有任务完成后再启动下一层。
                更利于调试、性能分析和阶段性资源控制。

        Raises
        ------
        ValueError
            如果输入图不合法或 layout_mode 参数错误。
        """
        self.set_root_stages(root_stages)

        self.init_env()
        self.init_structure_graph()
        self.analyze_graph()
        self.set_layout_mode(layout_mode)
        self.set_reporter()

    def init_env(self):
        """
        初始化环境
        """
        self.processes: List[multiprocessing.Process] = []

        self.init_dict()
        self.init_task_queues()
        self.init_log()

    def init_dict(self):
        """
        初始化字典
        """
        self.stages_status_dict: Dict[str, dict] = defaultdict(dict) # 用于保存每个节点的状态信息
        self.stage_extra_stats = defaultdict(dict) # 用于保存每个阶段的额外统计信息
        self.last_status_dict = {}  # 用于保存每个节点的最后状态信息

        self.edge_queue_map: Dict[Tuple[str, str], MPQueue] = {}  # 用于保存每个节点到下一个节点的队列
        
        self.stage_locks = {}  # 锁，用于控制每个阶段success_counter的并发
        self.stage_success_counter = {}  # 用于保存每个阶段成功处理的任务数
        self.stage_error_counter = {}  # 用于保存每个阶段失败处理的任务数
        self.stage_duplicate_counter = {}  # 用于保存每个阶段重复处理的任务数
        
        self.final_result_dict = {}  # 用于保存初始任务到最终结果的映射
        self.error_timeline_dict: Dict[str, list] = defaultdict(list)  # 用于保存错误到出现该错误任务的映射
        self.all_stage_error_dict: Dict[str, dict] = defaultdict(dict)  # 用于保存节点到节点失败任务的映射

    def init_task_queues(self):
        """
        初始化任务队列
        :param tasks: 待处理的任务列表
        """
        visited_stages = set()
        queue = deque(self.root_stages)  # BFS 用队列代替递归

        while queue:
            stage = queue.popleft()
            stage_tag = stage.get_stage_tag()
            if stage_tag in visited_stages:
                continue

            # 记录节点
            self.stages_status_dict[stage_tag]["stage"] = stage

            # 为每个边 (prev -> stage) 创建队列
            for prev_stage in stage.prev_stages:
                prev_tag = prev_stage.get_stage_tag() if prev_stage else None
                self.edge_queue_map[(prev_tag, stage_tag)] = MPQueue()

            if not stage.prev_stages:
                # 起点节点
                self.edge_queue_map[(None, stage_tag)] = MPQueue()

            visited_stages.add(stage_tag)

            for next_stage in stage.next_stages:
                queue.append(next_stage)

        self.fail_queue = MPQueue()

    def init_log(self):
        """
        初始化日志
        """
        self.log_listener = LogListener(level = "INFO")
        self.task_logger = TaskLogger(self.log_listener.get_queue())

    def init_structure_graph(self):
        """
        初始化任务图结构
        """
        self.structure_graph = build_structure_graph(self.root_stages)

    def set_root_stages(self, root_stages: List[TaskManager]):
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
        """
        self.is_report = is_report
        self.reporter = TaskReporter(self, self.log_listener.get_queue(), host, port)

    def set_graph_mode(self, stage_mode: str, execution_mode: str):
        """
        设置任务链的执行模式
        :param stage_mode: 节点执行模式, 可选值为 'serial' 或 'process'
        :param execution_mode: 节点内部执行模式, 可选值为 'serial' 或 'thread''
        """

        def set_subsequent_stage_mode(stage: TaskManager):
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
            prev_stage: TaskManager = self.stages_status_dict[tag]["stage"].prev_stages[0]
            prev_tag = prev_stage.get_stage_tag() if prev_stage else None
            for task in tasks:
                self.edge_queue_map[(prev_tag, tag)].put(make_hashable(task))
                if isinstance(task, TerminationSignal):
                    self.task_logger._log("TRACE", f"TERMINATION_SIGNAL put into {(prev_tag, tag)}")
                    continue
                self.task_logger._log("TRACE", f"{task} put into {(prev_tag, tag)}")
                self.stages_status_dict[tag]["init_tasks_num"] = self.stages_status_dict[tag].get("init_tasks_num", 0) + 1
        
        if put_termination_signal:
            for root_stage in self.root_stages:
                pre_stage_tag = root_stage.prev_stages[0].get_stage_tag() if root_stage.prev_stages[0] else None
                edge_key = (pre_stage_tag, root_stage.get_stage_tag())
                self.edge_queue_map[edge_key].put(TERMINATION_SIGNAL)
                self.task_logger._log("TRACE", f"TERMINATION_SIGNAL put into {edge_key}")

    def start_graph(self, init_tasks_dict: dict, put_termination_signal: bool=True):
        """
        启动任务链
        """
        try:
            self.log_listener.start()
            self.start_time = time.time()
            self.task_logger.start_graph(self.get_structure_list())
            self._persist_structure_metadata()
            self.reporter.start() if self.is_report else None

            self.put_stage_queue(init_tasks_dict, put_termination_signal)
            self._excute_stages()

        finally:
            self.finalize_nodes()
            self.reporter.stop()
            self.handle_fail_queue()
            self.release_resources()

            self.task_logger.end_graph(time.time() - self.start_time)
            self.log_listener.stop()

    def _excute_stages(self):
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
                    stage: TaskManager = self.stages_status_dict[stage_tag]["stage"]
                    self._execute_stage(stage)
                    if stage.stage_mode == "process":
                        processes.append(self.processes[-1])  # 最新的进程

                # join 当前层的所有进程（如果有）
                for p in processes:
                    p.join()
                    self.stages_status_dict[p.name]["status"] = StageStatus.STOPPED
                    self.task_logger._log("DEBUG", f"{p.name} exitcode: {p.exitcode}")

                self.task_logger.end_layer(layer, time.time() - start_time)

    def _execute_stage(self, stage: TaskManager):
        """
        递归地执行节点任务
        """
        stage_tag = stage.get_stage_tag()

        input_queues = []
        for prev_stage in stage.prev_stages:
            prev_tag = prev_stage.get_stage_tag() if prev_stage else None
            input_queues.append(self.edge_queue_map[(prev_tag, stage_tag)])

        if not stage.next_stages:
            output_queues = []
        else:
            output_queues = [
                self.edge_queue_map[(stage_tag, next_stage.get_stage_tag())]
                for next_stage in stage.next_stages
            ]
        logger_queue = self.log_listener.get_queue()

        self.stages_status_dict[stage_tag]["status"] = StageStatus.RUNNING
        self.stages_status_dict[stage_tag]["start_time"] = time.time()

        if isinstance(stage, TaskSplitter):
            self.stage_extra_stats[stage_tag]["split_output_count"] = MPValue("i", 0)
        else:
            self.stage_extra_stats[stage_tag] = {}

        if stage.stage_mode == "process":
            self.stage_success_counter[stage_tag] = MPValue("i", 0)
            self.stage_error_counter[stage_tag] = MPValue("i", 0)
            self.stage_duplicate_counter[stage_tag] = MPValue("i", 0)
            self.stage_locks[stage_tag] = MPLock()

            stage.init_counter(
                self.stage_success_counter[stage_tag],
                self.stage_error_counter[stage_tag],
                self.stage_duplicate_counter[stage_tag],
                self.stage_locks[stage_tag],
                self.stage_extra_stats[stage_tag]
            )
            p = multiprocessing.Process(
                target=stage.start_stage, args=(input_queues, output_queues, self.fail_queue, logger_queue), name=stage_tag
            )
            p.start()
            self.processes.append(p)
        else:
            self.stage_success_counter[stage_tag] = ValueWrapper()
            self.stage_error_counter[stage_tag] = ValueWrapper()
            self.stage_duplicate_counter[stage_tag] = ValueWrapper()

            stage.init_counter(
                self.stage_success_counter[stage_tag], 
                self.stage_error_counter[stage_tag],
                self.stage_duplicate_counter[stage_tag],
                None, 
                self.stage_extra_stats[stage_tag]
            )
            stage.start_stage(input_queues, output_queues, self.fail_queue, logger_queue)

            self.stages_status_dict[stage_tag]["status"]  = StageStatus.STOPPED

    def finalize_nodes(self):
        """
        确保所有子进程安全结束，更新节点状态，并导出每个节点队列剩余任务。
        返回: dict, {stage_tag: [剩余任务列表]}
        """
        # 1️⃣ 确保所有进程安全结束（不一定要 terminate，但如果没结束就强制）
        for p in self.processes:
            if p.is_alive():
                self.task_logger._log("WARNING", f"检测到进程 {p.name} 仍在运行, 尝试终止")
                p.terminate()
                p.join(timeout=5)
                if p.is_alive():
                    self.task_logger._log("WARNING", f"进程 {p.name} 仍未完全退出")
                self.task_logger._log("DEBUG", f"{p.name} exitcode: {p.exitcode}")

        # 2️⃣ 更新所有节点状态为“已停止”
        for stage_tag, stage_status in self.stages_status_dict.items():
            stage_status["status"] = StageStatus.STOPPED  # 已停止

        # 3️⃣ 收集并持久化每个 stage 中未消费的任务
        # for stage_tag, stage_status in self.stages_status_dict.items():
        #     queue: MPQueue = stage_status["task_queue"]
        #     while not queue.empty():
        #         try:
        #             task = queue.get_nowait()
        #             self.task_logger._log("DEBUG", f"获取 {stage_tag} 剩余任务: {task}")

        #             self._persist_unconsumed_task(stage_tag, task)
        #         except Exception as e:
        #             self.task_logger._log("WARNING", f"获取 {stage_tag} 剩余任务失败: {e}")

    def release_resources(self):
        """
        释放资源
        """
        for stage_status_dict in self.stages_status_dict.values():
            stage_status_dict["stage"].release_queue()

        cleanup_mpqueue(self.fail_queue)
        
    def process_final_result_dict(self, initial_tasks):
        """
        查找对应的初始任务并更新 final_result_dict (已废弃)

        :param initial_tasks: 一个包含初始任务的列表
        """

        def update_final_result_dict(stage_task, stage: TaskManager):
            stage_success_dict = stage.get_success_dict()
            stage_error_dict = all_stage_error_dict.get(stage.get_stage_tag(), {})
            visited_stages.add(stage)

            final_list = []
            if stage_task in stage_success_dict:
                stage_task = stage_success_dict[stage_task]
            elif stage_task in stage_error_dict:
                stage_task = stage_error_dict[stage_task]
                task_execution_status[initial_task] = False
                return [(stage_task, stage.get_stage_tag())]
            else:
                dispear_exception = TaskError(f"({stage_task}) not found.")
                task_execution_status[initial_task] = False
                return [(dispear_exception, stage.get_stage_tag())]

            if not stage.next_stages:
                return [(stage_task, stage.get_stage_tag())]

            for next_stage in stage.next_stages:
                if next_stage in visited_stages:
                    continue
                elif not isinstance(stage, TaskSplitter):
                    next_stage_final_list = update_final_result_dict(
                        stage_task, next_stage
                    )
                    final_list.extend(next_stage_final_list)
                    continue

                # 如果是 TaskSplitter，则递归处理每个子任务
                for split_task in stage_task:
                    next_stage_final_list = update_final_result_dict(
                        split_task, next_stage
                    )
                    final_list.extend(next_stage_final_list)

            return final_list

        task_execution_status = {}
        all_stage_error_dict = self.get_all_stage_error_dict()
        for initial_task in initial_tasks:
            visited_stages = set()
            task_execution_status[initial_task] = True
            self.final_result_dict[initial_task] = update_final_result_dict(
                initial_task, self.root_stage
            )

    def handle_fail_queue(self):
        """
        消费 fail_queue, 构建失败字典
        """
        while not self.fail_queue.empty():
            item: dict = self.fail_queue.get_nowait()
            stage_tag = item["stage_tag"]
            task_str = item["task"]
            error_info = item["error_info"]
            timestamp = item["timestamp"]
            error_key = (error_info, stage_tag)

            if task_str not in self.error_timeline_dict[error_key]:
                self.error_timeline_dict[error_key].append((task_str, timestamp))

            if task_str not in self.all_stage_error_dict[stage_tag]:
                self.all_stage_error_dict[stage_tag][task_str] = error_key

            self._persist_single_failure(task_str, error_info, stage_tag, timestamp)

    def _persist_structure_metadata(self):
        """
        在运行开始时写入任务结构元信息到 jsonl 文件
        """
        log_item = {
            "timestamp": datetime.now().isoformat(),
            "structure": self.get_structure_json(),
        }
        append_jsonl_log(log_item, self.start_time, "./fallback", "realtime_errors", self.task_logger)

    def _persist_single_failure(self, task_str, error_info, stage_tag, timestamp):
        """
        增量写入单条错误日志到每日文件中
        """
        log_item = {
            "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
            "stage": stage_tag,
            "error": error_info,
            "task": task_str,
        }
        append_jsonl_log(log_item, self.start_time, "./fallback", "realtime_errors", self.task_logger)

    def _persist_unconsumed_task(self, stage_tag, task):
        """
        写入单个未消费任务到 JSONL 文件
        """
        log_item = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage_tag,
            "task": str(task)
        }
        append_jsonl_log(log_item, self.start_time, "./fallback", "leftover_tasks", self.task_logger)

    def get_stages_status_dict(self):
        """
        返回节点状态字典
        """
        return dict(self.stages_status_dict)

    def get_final_result_dict(self):
        """
        返回最终结果字典
        """
        return self.final_result_dict

    def get_error_timeline_dict(self):
        """
        返回最终错误字典
        """
        return dict(self.error_timeline_dict)

    def get_all_stage_error_dict(self):
        """
        返回最终失败字典
        """
        return dict(self.all_stage_error_dict)
    
    def get_fail_by_error_dict(self):
        return {
            key: [a for a, _ in tuple_list]
            for key, tuple_list in self.get_error_timeline_dict().items()
        }

    def get_fail_by_stage_dict(self):
        return {
            stage: list(inner_dict.keys())
            for stage, inner_dict in self.get_all_stage_error_dict().items()
        }
    
    def get_status_dict(self) -> dict:
        """
        获取任务链的状态字典
        """
        status_dict = {}
        now = time.time()
        interval = self.reporter.interval

        for tag, stage_status_dict in self.stages_status_dict.items():
            stage: TaskManager = stage_status_dict["stage"]
            last_stage_status_dict: dict = self.last_status_dict.get(tag, {})

            total_input = stage_status_dict.get("init_tasks_num", 0)
            
            for prev in stage.prev_stages:
                if not prev:
                    break
                prev_tag = prev.get_stage_tag()
                if isinstance(prev, TaskSplitter):
                    total_input += self.stage_extra_stats[prev_tag].get("split_output_count", ValueWrapper()).value
                else:
                    total_input += self.stage_success_counter.get(prev_tag, ValueWrapper()).value

            status         = stage_status_dict.get("status", StageStatus.NOT_STARTED)
            successed      = self.stage_success_counter.get(tag, ValueWrapper()).value
            failed         = self.stage_error_counter.get(tag, ValueWrapper()).value
            duplicated     = self.stage_duplicate_counter.get(tag, ValueWrapper()).value
            pending        = max(0, total_input - successed - failed - duplicated)

            add_successed  = successed - last_stage_status_dict.get("tasks_successed", 0)
            add_failed     = failed - last_stage_status_dict.get("tasks_failed", 0)
            add_duplicated = duplicated - last_stage_status_dict.get("tasks_duplicated", 0)
            add_pending    = pending - last_stage_status_dict.get("tasks_pending", 0)

            start_time     = stage_status_dict.get("start_time", 0)
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
            remaining = (elapsed / (successed + failed + duplicated) * pending) if (successed or failed or duplicated) and pending else 0

            # 计算平均时间（秒/任务）并格式化为字符串
            if successed or failed or duplicated:
                avg_time = elapsed / (successed + failed + duplicated)
                if avg_time >= 1.0:
                    # 显示 "X.XX s/it"
                    avg_time_str = f"{avg_time:.2f}s/it"
                else:
                    # 显示 "X.XX it/s"（取倒数）
                    its_per_sec = (successed + failed + duplicated) / elapsed if elapsed else 0
                    avg_time_str = f"{its_per_sec:.2f}it/s"
            else:
                avg_time_str = "N/A"  # 或 "0.00s/it" 根据需求

            history: list = stage_status_dict.get("history", [])
            history.append({
                "timestamp": now,
                "tasks_processed": successed+failed+duplicated,
            })
            history.pop(0) if len(history) > 20 else None
            stage_status_dict["history"] = history

            status_dict[tag] = {
                **stage.get_stage_summary(),
                "status": status,

                "tasks_successed": successed,
                "tasks_failed": failed,
                "tasks_duplicated": duplicated,
                "tasks_processed": successed+failed+duplicated,
                "tasks_pending": pending,

                "add_tasks_successed": add_successed,
                "add_tasks_failed": add_failed,
                "add_tasks_duplicated": add_duplicated,
                "add_tasks_processed": add_successed+add_failed+add_duplicated,
                "add_tasks_pending": add_pending,

                "start_time": format_timestamp(start_time),
                "elapsed_time": format_duration(elapsed),
                "remaining_time": format_duration(remaining),
                "task_avg_time": avg_time_str,
                "history": history
            }

        self.last_status_dict = status_dict

        return status_dict
    
    def get_graph_topology(self):
        return {
            "isDAG": self.isDAG,
            "layout_mode": self.layout_mode,
            "class_name": self.__class__.__name__,
            "layers_dict": self.layers_dict,
        }
    
    def get_structure_json(self):
        return self.structure_graph
    
    def get_structure_list(self):
        return format_structure_list_from_graph(self.structure_graph)
    
    def get_networkx_graph(self):
        return format_networkx_graph(self.structure_graph)
    
    def analyze_graph(self):
        networkx_graph = self.get_networkx_graph()
        self.layers_dict = {}

        self.isDAG = is_directed_acyclic_graph(networkx_graph)
        if self.isDAG:
            self.stage_level_dict = compute_node_levels(networkx_graph)
            self.layers_dict = cluster_by_value_sorted(self.stage_level_dict)

    def test_methods(self, init_tasks_dict: Dict[str, List], stage_modes: list=None, execution_modes: list=None) -> Dict[str, Any]:
        """
        测试 TaskGraph 在 'serial' 和 'process' 模式下的执行时间。

        :param init_tasks_dict: 初始化任务字典
        :param stage_modes: 阶段模式列表，默认为 ['serial', 'process']
        :param execution_modes: 执行模式列表，默认为 ['serial', 'thread']
        :return: 包含两种执行模式下的执行时间的字典
        """
        results = {}
        test_table_list = []
        # final_result_dict = {}
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

                time_list.append(time.time() - start_time)
                # final_result_dict.update(self.get_final_result_dict())
                fail_by_error_dict.update(self.get_fail_by_error_dict())
                fail_by_stage_dict.update(self.get_fail_by_stage_dict())

            test_table_list.append(time_list)

        results["Time table"] = (
            test_table_list,
            execution_modes,
            stage_modes,
            r"stage\execution",
        )
        # results["Final result dict"] = final_result_dict
        results["Fail error dict"] = fail_by_error_dict
        results["Fail stage dict"] = fail_by_stage_dict
        return results
