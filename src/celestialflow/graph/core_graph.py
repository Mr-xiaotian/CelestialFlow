# graph/core_graph.py
from __future__ import annotations

import asyncio
import threading
import time
import uuid
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from ..assembly import run_resources
from ..node.util_types import AnyTaskNode
from ..observer import (
    GraphEndEvent,
    GraphStartEvent,
    Observer,
    ObserverHub,
)
from ..persist.util_sqlite import (
    load_tasks_grouped_by_node,
)
from ..reporter import MetricsObserver, NullTaskReporter, ReporterProtocol
from ..runtime.util_errors import (
    ConfigurationError,
    DuplicateNodeError,
    InvalidOptionError,
    NodeNotFoundError,
    UnknownNodeError,
)
from ..runtime.util_event import EventClient, LocalEventClient
from ..runtime.util_format import cluster_by_value_sorted
from .util_order_graph import OrderGraph, compute_node_levels, is_dag, source_nodes
from .util_render import render_structure_list


class TaskGraph:
    """任务图核心类，负责构建、连接和调度一组任务节点。

    注意：
    - ``start()`` / ``start_async()`` 为一次性调用；启动并运行完成后，不保证当前实例可
      被安全重置或重复启动。如需再次运行相同流程，请重新创建 TaskGraph 实例及其关联的
      节点对象。
    - 构建期方法（``set_nodes`` / ``connect`` / ``set_graph_mode`` / ``set_node_execution_mode`` 等）
      在启动前可多次调用，图分析缓存会随之按需重建（``_analysis_dirty`` 标记）。
    """

    # ==== 类级类型注解 ====
    name: str
    graph_id: str
    graph_mode: str
    threads: list[threading.Thread]
    node_dict: dict[str, AnyTaskNode]
    _analysis_dirty: bool
    source_names: list[str]
    order_graph: OrderGraph
    start_time: float
    observers: ObserverHub
    metrics: MetricsObserver
    reporter: ReporterProtocol
    ctree_client: EventClient
    is_dag: bool
    layers_dict: dict[int, list[str]]
    _lifecycle_db_path: Path | None

    # ==== 初始化 ====

    def __init__(
        self,
        name: str,
        graph_mode: str = "serial",
    ) -> None:
        """
        初始化 TaskGraph 实例。

        TaskGraph 表示一组任务节点所构成的任务图，可用于构建并行、串行、
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
        self.node_dict = {}

        # 用于保存源节点列表（由 _build_analysis 自动计算）
        self.source_names = []

        # 用于保存图结构的邻接表
        self.order_graph = OrderGraph()
        self._analysis_dirty = True

        # 用于保存任务图启动时间
        self.start_time = 0.0

        # 用于保存观察者
        self.observers = ObserverHub()

        # 用于保存图级指标写模型；建图期即注册，确保节点/连接结构事件不丢失
        self.metrics = MetricsObserver()
        self.observers.add_observer(self.metrics)

        # 用于保存生命周期数据库路径
        self._lifecycle_db_path = None

    # ==== 建图 ====

    def set_nodes(self, nodes: list[AnyTaskNode]) -> None:
        """
        添加节点到任务图中

        :param nodes: 待添加的节点列表
        :raises DuplicateNodeError: 存在重复的节点名称
        """
        for node in nodes:
            node_name = node.get_name()
            if node_name in self.node_dict:
                raise DuplicateNodeError(f"duplicate node name: {node_name}")
            self.node_dict[node_name] = node
            self.order_graph.add_node(node_name)

            node.set_ctree(self.ctree_client)
            self.observers.on_node_added(node_name)

        self._analysis_dirty = True

    def connect[R](
        self,
        from_nodes: list[AnyTaskNode],
        to_nodes: list[AnyTaskNode],
    ) -> None:
        """
        建立超边连接：`from_nodes` 中的每个节点连接到 `to_nodes` 中的每个节点。

        :param from_nodes: 上游节点列表
        :param to_nodes: 下游节点列表
        """
        for from_node in from_nodes:
            from_name = from_node.get_name()
            if from_name not in self.node_dict:
                raise NodeNotFoundError(f"from node not found: {from_name}")

            for to_node in to_nodes:
                to_name = to_node.get_name()
                if to_name not in self.node_dict:
                    raise NodeNotFoundError(f"to node not found: {to_name}")

                from_node.connect_to(to_node)
                self.order_graph.add_edge(from_name, to_name)
                self.observers.on_node_connected(from_name, to_name)

        self._analysis_dirty = True

    # ==== 配置 ====

    def _set_name(self, name: str) -> None:
        """
        设置任务图名称，并生成该运行实例的不透明唯一标识。

        :param name: 任务图名称
        """
        self.name = name
        self.graph_id = uuid.uuid4().hex

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

    def set_node_execution_mode(self, execution_mode: str) -> None:
        """
        设置任务链的执行模式

        :param execution_mode: 节点内部执行模式, 可选值为 'serial', 'thread' 或 'async'
        """
        for node in self.node_dict.values():
            node.set_execution_mode(execution_mode)
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
        if not hasattr(self, "node_dict"):
            return
        for node in self.node_dict.values():
            node.set_ctree(ctree_client)

    # ==== 观察者 ====

    def add_observer(self, observer: Observer) -> None:
        """
        注册图级观察者。

        图级观察者会收到图中所有节点的事件；该注册仅在 :meth:`run` /
        :meth:`run_async` 路径下生效（这两个入口会把图级 hub 注入每个节点）。

        若注册发生在建图之后，会向该观察者回放当前图结构（``on_node_added`` /
        ``on_node_connected``），保证结构类观察者不因注册顺序而遗漏拓扑。

        :param observer: 要注册的观察者实例
        """
        self.observers.add_observer(observer)

        if isinstance(observer, ObserverHub):
            return
        try:
            for node_name in self.order_graph.nodes:
                observer.on_node_added(node_name)
            for from_name, to_names in self.order_graph.out_edges.items():
                for to_name in to_names:
                    observer.on_node_connected(from_name, to_name)
        except Exception as e:
            observer.handle_exception(e)

    def _inject_observers(self) -> None:
        """
        将图级观察者 hub 注入每个节点。

        注入的是 hub 对象本身，因此运行期往图级 hub 增删观察者会立即对所有节点生效。
        必须在灌入初始任务之前调用，否则初始任务的输入事件不会分发给图级观察者。
        """
        for node in self.node_dict.values():
            node.observers.add_observer(self.observers)

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

        node_level_dict = compute_node_levels(self.order_graph)
        self.layers_dict = cluster_by_value_sorted(node_level_dict)
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
            self.node_dict[source_name].put_signal()

    # ==== 执行 ====

    def run(
        self,
        init_tasks_dict: dict[str, Iterable[Any]],
        *,
        if_put_signal: bool = True,
    ) -> None:
        """
        运行任务链，注入初始任务并启动执行。

        本方法负责实例化运行期资源：注入图级观察者、注册全局 funnel 观察者、
        启动全局 ``lifecycle`` / ``log`` spout，注入任务后交由 :meth:`start` 处理，
        最后统一收尾。

        :param init_tasks_dict: 任务列表字典，键为节点名称，值为任务列表
        :param if_put_signal: 是否注入终止信号，默认 True
        :return: ``None``
        """
        self._build_analysis()
        self._inject_observers()

        error_list: list[Exception] = []

        try:
            with run_resources(
                self.observers, self.graph_id, self.metrics
            ) as lifecycle_db_path:
                self._lifecycle_db_path = lifecycle_db_path
                for node_name, tasks in init_tasks_dict.items():
                    for task in tasks:
                        self.node_dict[node_name].put_task(task)
                if if_put_signal:
                    self.put_source_signal()
                self.start()
        except Exception as exception:
            error_list.append(exception)

        if error_list:
            raise ExceptionGroup("Errors occurred during run", error_list)

    async def run_async(
        self,
        init_tasks_dict: dict[str, Iterable[Any]],
        *,
        if_put_signal: bool = True,
    ) -> None:
        """
        运行任务链，注入初始任务并启动执行。

        运行期资源的实例化与收尾同 :meth:`run`，区别仅在于以协程方式启动。

        :param init_tasks_dict: 初始任务字典，键为节点名称，值为任务可迭代对象
        :param if_put_signal: 是否注入终止信号，默认 True
        :return: ``None``
        """
        self._build_analysis()
        self._inject_observers()

        error_list: list[Exception] = []

        try:
            with run_resources(
                self.observers, self.graph_id, self.metrics
            ) as lifecycle_db_path:
                self._lifecycle_db_path = lifecycle_db_path
                for node_name, tasks in init_tasks_dict.items():
                    for task in tasks:
                        self.node_dict[node_name].put_task(task)
                if if_put_signal:
                    self.put_source_signal()
                await self.start_async()
        except Exception as exception:
            error_list.append(exception)

        if error_list:
            raise ExceptionGroup("Errors occurred during run", error_list)

    def restore_db(
        self,
        db_path: str | Path,
        statuses: Iterable[str] | None = None,
        *,
        filter_by_error_type: bool = False,
        if_put_signal: bool = True,
    ) -> None:
        """
        从 sqlite 持久化库中读取任务，按持久化记录中的节点名分组后启动任务图。

        :param db_path: sqlite 数据库文件路径
        :param statuses: 记录状态过滤列表，默认 ``["failed", "pending"]``
        :param filter_by_error_type: 是否按各节点的 ``retry_exceptions`` 过滤
            ``error_type``，默认 ``False``
        :param if_put_signal: 是否在恢复任务注入后，为所有源节点补发终止信号，
            默认 ``True``
        """
        statuses = ["failed", "pending"] if statuses is None else statuses
        grouped_records = load_tasks_grouped_by_node(db_path, statuses)
        tasks: dict[str, Iterable[Any]] = {}

        for name, records in grouped_records.items():
            node = self.node_dict[name]
            if filter_by_error_type and name in self.node_dict:
                retry_error_type_names = node.get_retry_error_type_names()
                records = [
                    record
                    for record in records
                    if str(record["error_type"]) in retry_error_type_names
                    or record["status"] == "pending"
                ]
            tasks[name] = [record["task_json"] for record in records]

        self.run(tasks, if_put_signal=if_put_signal)

    # ==== 启动 ====

    def _prepare_start(self) -> None:
        """
        启动前准备：图分析、必要警告与运行时资源启动。

        本方法会创建线程与文件句柄等运行时资源，调用方应保证在 finally 中
        执行 :meth:`_finish_start` 完成收尾。

        :return: ``None``
        """
        self.observers.on_graph_start(
            GraphStartEvent(
                graph=self.name,
                graph_mode=self.graph_mode,
                start_time=self.start_time,
                class_name=self.__class__.__name__,
                is_dag=self.is_dag,
                nodes=self.get_nodes(),
                edges=self.get_edges(),
                source_nodes=self.get_source_nodes(),
                node_meta=self.get_node_meta(),
                structure_list=self.get_structure_list(),
            )
        )
        self.reporter.start()

    def _finish_start(self, start_perf: float) -> list[Exception]:
        """
        启动后收尾：回收图内状态、停止上报器并记录结束日志。

        ``lifecycle`` / ``log`` / 错误上报 spout 的启停由外层 :meth:`run` /
        :meth:`run_async` 统一管理，本方法只负责图对象自身的收尾逻辑。

        :param start_perf: 启动时刻的 ``perf_counter`` 时间戳，用于计算运行耗时
        :return: 收集到的收尾阶段异常列表
        """
        error_list: list[Exception] = []

        try:
            # 收集并持久化每个节点中未消费的任务
            for node in self.node_dict.values():
                node.drain_task_queue()
        except Exception as exception:
            error_list.append(exception)

        try:
            self.reporter.stop()
        except Exception as exception:
            error_list.append(exception)

        try:
            self.observers.on_graph_end(
                GraphEndEvent(
                    graph=self.name,
                    elapsed=time.perf_counter() - start_perf,
                )
            )
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
          同步路径仍会通过 ``asyncio.run`` 启动该节点，可能触发 ``asyncio.run`` 的
          嵌套限制；此时更适合使用 :meth:`start_async` 或 :meth:`run_async`。
        - 图级观察者（:meth:`add_observer`）仅在 :meth:`run` / :meth:`run_async`
          路径下注入；直接调用本方法时图级观察者不会生效。

        :note:
            ``start()`` 为一次性调用；构建期方法在启动前可多次调用。
        """
        start_perf = time.perf_counter()
        self.start_time = time.time()
        error_list: list[Exception] = []

        try:
            self._prepare_start()

            if self.graph_mode == "serial":
                self._execute_nodes_serial()
            elif self.graph_mode == "thread":
                self._execute_nodes_thread()
            else:
                raise InvalidOptionError(
                    "graph mode", self.graph_mode, ("serial", "thread")
                )
        except Exception as exception:
            error_list.append(exception)
        finally:
            finish_errors = self._finish_start(start_perf)
            error_list.extend(finish_errors)

        if error_list:
            raise ExceptionGroup("Errors occurred during graph execution", error_list)

    async def start_async(self) -> None:
        """
        以异步方式启动任务图，适合在已运行事件循环的上下文中调用。

        与同步 :meth:`start` 的区别：
        - async 执行模式的节点通过 :meth:`TaskExecutor.start_async` 以协程方式运行，
          本路径不会在节点内部再调用 ``asyncio.run``，避免嵌套事件循环导致的崩溃；
          同步 :meth:`start` 路径则会为 ``async`` 节点调用 ``asyncio.run``，参见对应文档。
        - serial / thread 执行模式的节点通过 ``asyncio.to_thread`` 在独立线程中运行，
          避免阻塞事件循环。
        :note:
            ``start_async()`` 为一次性调用；构建期方法在启动前可多次调用。
        """
        if self.graph_mode != "async":
            raise InvalidOptionError("graph mode", self.graph_mode, ("async",))

        start_perf = time.perf_counter()
        self.start_time = time.time()
        error_list: list[Exception] = []

        try:
            self._prepare_start()
            await self._execute_nodes_async()
        except Exception as exception:
            error_list.append(exception)
        finally:
            finish_errors = self._finish_start(start_perf)
            error_list.extend(finish_errors)

        if error_list:
            raise ExceptionGroup("Errors occurred during graph execution", error_list)

    def _execute_nodes_serial(self) -> None:
        """
        以串行方式按层展开的拓扑序执行所有节点。

        层间按层级升序、层内按注册顺序逐个执行，每个节点执行完毕后才
        启动下一个。层展开序保证每个节点的所有上游都先于它启动，因此
        执行顺序不再依赖节点注册顺序。

        注：图分析（:attr:`layers_dict`）由 :meth:`_prepare_start` 经
        :meth:`get_structure_list` 保证已构建。
        """
        for node_name_list in self.layers_dict.values():
            for node_name in node_name_list:
                node = self.node_dict[node_name]
                self._execute_node(node)

    def _execute_nodes_thread(self) -> None:
        """
        以线程方式并发执行所有节点。

        每个节点在独立线程中启动，最后统一等待所有线程结束。
        """
        for node in self.node_dict.values():
            t = threading.Thread(
                target=self._execute_node,
                args=(node,),
                name=node.get_name(),
                daemon=True,
            )
            t.start()
            self.threads.append(t)

        for t in self.threads:
            t.join()

    async def _execute_nodes_async(self) -> None:
        """
        异步执行所有节点：全图并发执行。
        """
        tasks = [
            asyncio.create_task(self._execute_node_async(node))
            for node in self.node_dict.values()
        ]
        await asyncio.gather(*tasks)

    def _execute_node(self, node: AnyTaskNode) -> None:
        """
        在同步图启动路径下执行单个节点。

        :param node: 节点
        """
        if node.execution_mode == "async":
            asyncio.run(node.start_async())
        else:
            node.start()

    async def _execute_node_async(self, node: AnyTaskNode) -> None:
        """
        异步执行单个节点：async 模式走协程，其余模式走线程池。

        :param node: 节点
        """
        if node.execution_mode == "async":
            await node.start_async()
        else:
            await asyncio.to_thread(node.start)

    # ==== 查询接口 ====

    def get_graph_id(self) -> str:
        """
        获取当前任务图实例的唯一标识。

        :return: graph_id
        """
        return self.graph_id

    def get_nodes(self) -> list[str]:
        """
        获取所有任务节点的名称列表

        :return: 任务节点名称列表
        """
        return self.order_graph.nodes

    def get_edges(self) -> dict[str, list[str]]:
        """
        获取任务图的边邻接表。

        :return: 边信息邻接表 ``{node_name: [next_node_name, ...]}``；
            与底层图结构共享引用，调用方应只读
        """
        return self.order_graph.out_edges

    def get_node_meta(self) -> dict[str, dict[str, Any]]:
        """
        获取各节点的构建期元信息。

        这些字段在 reporter 启动前已冻结，因此随图结构一次性上报，不进每轮状态推送。

        :return: ``{node_name: {"class_name": ..., "execution_mode": ..., "max_workers": ...}}``
        """
        return {
            node_name: node.get_meta() for node_name, node in self.node_dict.items()
        }

    def get_source_nodes(self) -> list[str]:
        """
        获取源节点列表

        :return: 源节点列表
        """
        self._ensure_analysis()
        return self.source_names

    def get_structure_list(self) -> list[str]:
        """
        获取任务图的格式化结构列表

        :return: 带边框的格式化字符串列表
        """
        self._ensure_analysis()
        return render_structure_list(
            self.get_nodes(),
            self.get_edges(),
            self.get_source_nodes(),
        )

    def get_order_graph(self) -> OrderGraph:
        """
        获取任务图对应的有序有向图视图。

        :return: :class:`OrderGraph` 实例
        """
        return self.order_graph

    def get_observers(self) -> ObserverHub:
        """
        获取图级观察者 hub。

        供节点以外的协作者（如 reporter）以观察者形式发布事件。

        :return: 图级观察者 hub
        """
        return self.observers

    # ==== Reporter 能力接口 ====

    def get_status_snapshot(self) -> dict[str, dict[str, Any]]:
        """
        采集各节点当前的运行时快照。

        计数与状态来自图级指标写模型，``start_time`` 等节点侧字段由此处补全。

        :return: ``{node_name: snapshot}``
        """
        metrics = self.metrics.get_graph_metrics()
        snapshot: dict[str, dict[str, Any]] = {}
        for node_name, node in self.node_dict.items():
            node_metrics = metrics.get(node_name)
            entry: dict[str, Any] = {"start_time": node.start_time}
            if node_metrics is not None:
                entry.update(
                    {
                        "status": node_metrics.status,
                        "tasks_input": node_metrics.input_total,
                        "tasks_succeeded": node_metrics.succeeded,
                        "tasks_failed": node_metrics.failed,
                        "tasks_skipped": node_metrics.skipped,
                        "tasks_processed": node_metrics.processed,
                        "tasks_pending": node_metrics.pending,
                        "upstream_counts": node_metrics.upstream_counts,
                        "downstream_counts": node_metrics.downstream_counts,
                    }
                )
            snapshot[node_name] = entry
        return snapshot

    def inject_tasks(self, tasks: Mapping[str, Sequence[Any]]) -> None:
        """
        按节点名将注入任务写入待执行队列。

        先为图中存在的节点尽力注入，再对未知节点统一报错，因此单个未知节点
        不会导致其余节点的任务被丢弃。

        :param tasks: 节点名到任务序列的映射
        :raises UnknownNodeError: 存在图中不存在的目标节点
        """
        missing_nodes: list[str] = []
        for target_node, task_datas in tasks.items():
            if target_node not in self.node_dict:
                missing_nodes.append(target_node)
                continue
            node = self.node_dict[target_node]
            for task in task_datas:
                node.put_task(task)

        if missing_nodes:
            raise UnknownNodeError(
                f"unknown target node(s) for task injection: {missing_nodes}"
            )

    def inject_terminations(self, nodes: Sequence[str]) -> None:
        """
        向指定节点注入终止信号。

        先为图中存在的节点尽力注入，再对未知节点统一报错，因此单个未知节点
        不会导致其余节点的终止信号被丢弃。

        :param nodes: 待注入终止符的节点名序列
        :raises UnknownNodeError: 存在图中不存在的目标节点
        """
        missing_nodes: list[str] = []
        for target_node in nodes:
            if target_node not in self.node_dict:
                missing_nodes.append(target_node)
                continue
            self.node_dict[target_node].put_signal()

        if missing_nodes:
            raise UnknownNodeError(
                f"unknown target node(s) for termination injection: {missing_nodes}"
            )
