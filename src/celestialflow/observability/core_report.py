# observability/core_report.py
from threading import Event, Thread
from typing import Any, cast

import requests

from ..graph.util_types import ReporterTaskGraph
from ..persistence import LogInlet
from ..persistence.util_sqlite import (
    get_event_ids,
    load_records,
    load_records_by_event_ids,
)
from ..runtime.util_errors import ReporterError
from ..runtime.util_types import TERMINATION_SIGNAL


class TaskReporter:
    """
    周期性向远程服务推送任务运行状态的上报器。

    - 定时从服务器拉取配置（如上报间隔、任务注入信息）
    - 将任务图中的状态、错误、结构、拓扑等信息推送到后端接口
    - 以后台线程方式运行，可随时 start()/stop()
    - 主要用于可视化监控、任务远程控制与 Web UI 同步
    """

    # ==== 生命周期 ====
    def __init__(
        self,
        host: str,
        port: int,
        task_graph: ReporterTaskGraph,
        log_inlet: LogInlet,
    ) -> None:
        """
        初始化任务上报器

        :param host: 远程服务主机地址
        :param port: 远程服务端口
        :param task_graph: 任务图实例
        :param log_inlet: 日志收集器实例
        """
        self.base_url: str = f"http://{host}:{port}"
        self.task_graph: ReporterTaskGraph = task_graph
        self.log_inlet: LogInlet = log_inlet

        self._stop_flag: Event = Event()
        self._thread: Thread | None = None
        self._session: requests.Session = requests.Session()
        self._server_has_current_graph: bool = False
        self._server_has_structure: bool = False
        self._server_has_analysis: bool = False
        self._server_event_ids: set[int] = set()

        self.interval: int = 5
        self.history_limit: int = 20

    def start(self) -> None:
        """启动上报器线程"""
        self._stop_flag.clear()
        self._thread = Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止上报器线程"""
        self._stop_flag.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        self._refresh_all()  # 最后一次
        self._session.close()
        self.log_inlet.stop_reporter()

    def _pull_timeout(self) -> float:
        """计算拉取请求的超时时间"""
        return max(1.0, min(self.interval * 0.2, 5.0))

    def _push_timeout(self) -> float:
        """计算推送请求的超时时间"""
        return max(1.0, min(self.interval * 0.2, 3.0))

    # ==== 循环 ====
    def _loop(self) -> None:
        """上报器主循环"""
        while not self._stop_flag.is_set():
            try:
                self._refresh_all()
            except Exception as e:
                self.log_inlet.loop_failed(e)
            _ = self._stop_flag.wait(self.interval)

    def _refresh_all(self) -> None:
        """刷新所有上报内容"""
        # 拉取逻辑
        self._pull_server_state()
        self._pull_and_inject_tasks()

        # 收集最新的任务图状态快照，确保推送的数据是最新的
        self.task_graph.collect_runtime_snapshot()

        # 推送逻辑
        if (not self._server_has_current_graph) or (not self._server_has_structure):
            self._push_structure()
        if (not self._server_has_current_graph) or (not self._server_has_analysis):
            self._push_analysis()
        self._push_status()
        self._push_errors()

    # ==== 拉取 ====
    def _pull_server_state(self) -> None:
        """从远程服务拉取同步决策所需的状态。"""
        try:
            res = self._session.get(
                f"{self.base_url}/api/pull_server_state",
                params={"graph_id": self.task_graph.get_graph_id()},
                timeout=self._pull_timeout(),
            )
            if not res.ok:
                raise ReporterError(f"Failed to pull server state: {res.status_code}")

            payload = res.json()
            interval: Any = payload.get("interval", 5)
            self.interval = int(max(1.0, min(float(interval), 60.0)))
            self._server_has_current_graph = bool(
                payload.get("is_current_graph", False)
            )
            self._server_has_structure = bool(payload.get("has_structure", False))
            self._server_has_analysis = bool(payload.get("has_analysis", False))
            event_ids = cast(list[Any], payload.get("event_ids", []) or [])
            self._server_event_ids = {int(event_id) for event_id in event_ids}
        except Exception as e:
            self.log_inlet.pull_interval_failed(e)

    def _pull_and_inject_tasks(self) -> None:
        """从远程服务拉取任务注入信息并注入任务"""
        try:
            res = self._session.get(
                f"{self.base_url}/api/pull_task_injection", timeout=self._pull_timeout()
            )
            if not res.ok:
                raise ReporterError(f"Failed to pull task injection: {res.status_code}")
        except Exception as e:
            self.log_inlet.pull_tasks_failed(e)
            return

        injection_tasks: dict[str, list[Any]] = res.json()
        tasks_by_stage = {
            target_stage: [
                task if task != "TERMINATION_SIGNAL" else TERMINATION_SIGNAL
                for task in task_datas
            ]
            for target_stage, task_datas in injection_tasks.items()
        }
        if not tasks_by_stage:
            return

        try:
            self.task_graph.put_stage_queue(
                tasks_by_stage, put_termination_signal=False
            )
            for target_stage, task_datas in tasks_by_stage.items():
                self.log_inlet.inject_tasks_success(target_stage, task_datas)
        except Exception as e:
            for target_stage, task_datas in tasks_by_stage.items():
                self.log_inlet.inject_tasks_failed(target_stage, task_datas, e)

    # ==== 推送 ====
    def _push_errors(self) -> None:
        """推送错误信息"""
        try:
            fallback_path = self.task_graph.get_fallback_path()
            graph_id = self.task_graph.get_graph_id()
            local_event_ids = get_event_ids(fallback_path) if fallback_path else []

            if not local_event_ids or not fallback_path:
                return

            if self._server_has_current_graph:
                missing_event_ids = [
                    event_id
                    for event_id in local_event_ids
                    if event_id not in self._server_event_ids
                ]
                if not missing_event_ids:
                    return
                append_mode = True
            else:
                missing_event_ids = local_event_ids
                append_mode = False

            self._push_errors_content(
                fallback_path,
                graph_id,
                missing_event_ids,
                append_mode,
            )

        except Exception as e:
            self.log_inlet.push_errors_failed(e)

    def _push_errors_content(
        self,
        fallback_path: str,
        graph_id: str,
        event_ids: list[int],
        append: bool,
    ) -> None:
        """
        推送错误内容（仅传本轮缺失的 ``event_id`` 对应条目）

        :param fallback_path: 错误存储文件路径
        :param graph_id: 当前任务图唯一标识
        :param event_ids: 本轮需要同步的失败事件 ``event_id`` 列表
        :param append: 是否以追加模式写入
        :return: None
        """
        all_errors: list[dict[str, Any]] = (
            load_records_by_event_ids(db_path=fallback_path, event_ids=event_ids)
            if append
            else load_records(db_path=fallback_path)
        )

        payload: dict[str, Any] = {
            "graph_id": graph_id,
            "event_ids": event_ids,
            "append": append,
            "errors": all_errors,
        }
        response: requests.Response = self._session.post(
            f"{self.base_url}/api/push_errors_content",
            json=payload,
            timeout=self._push_timeout(),
        )
        resp = response.json()
        if resp.get("ok"):
            pass
        else:
            raise ReporterError(
                f"push_errors_content failed: {resp.get('msg')}"
            )

    def _push_status(self) -> None:
        """推送状态信息"""
        try:
            payload: dict[str, Any] = self.task_graph.get_status_snapshot()
            payload["graph_id"] = self.task_graph.get_graph_id()
            _ = self._session.post(
                f"{self.base_url}/api/push_status",
                json=payload,
                timeout=self._push_timeout(),
            )
        except Exception as e:
            self.log_inlet.push_status_failed(e)

    def _push_structure(self) -> None:
        """推送结构信息"""
        try:
            structure: dict[str, Any] = self.task_graph.get_structure_graph()
            payload: dict[str, Any] = {
                "graph_id": self.task_graph.get_graph_id(),
                "structure": structure,
            }
            _ = self._session.post(
                f"{self.base_url}/api/push_structure",
                json=payload,
                timeout=self._push_timeout(),
            )
        except Exception as e:
            self.log_inlet.push_structure_failed(e)

    def _push_analysis(self) -> None:
        """推送分析信息"""
        try:
            analysis: dict[str, Any] = self.task_graph.get_graph_analysis()
            payload: dict[str, Any] = {
                "graph_id": self.task_graph.get_graph_id(),
                "analysis": analysis,
            }
            _ = self._session.post(
                f"{self.base_url}/api/push_analysis",
                json=payload,
                timeout=self._push_timeout(),
            )
        except Exception as e:
            self.log_inlet.push_analysis_failed(e)


class NullTaskReporter:
    """空实现的任务上报器，用于关闭上报功能时的占位对象。"""

    interval: int = 1
    history_limit: int = 20

    def start(self) -> None:
        """启动上报器线程"""
        return None

    def stop(self) -> None:
        """停止上报器线程"""
        return None
