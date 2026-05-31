# observability/core_report.py
from threading import Event, Thread
from typing import TYPE_CHECKING, Any

import requests

from ..persistence import LogInlet
from ..persistence.util_jsonl import load_jsonl_logs
from ..runtime.util_errors import ReporterError
from ..runtime.util_types import TERMINATION_SIGNAL

if TYPE_CHECKING:
    from ..graph import TaskGraph


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
        task_graph: "TaskGraph",
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
        self.task_graph: TaskGraph = task_graph
        self.log_inlet: LogInlet = log_inlet

        self._stop_flag: Event = Event()
        self._thread: Thread | None = None
        self._push_errors_mode: str = "meta"
        self._last_pushed_errors_rev: int | None = None
        self._session: requests.Session = requests.Session()

        self.interval: int = 5
        self.history_limit: int = 20

    def start(self) -> None:
        """启动上报器线程"""
        self._stop_flag.clear()
        self._thread = Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止上报器线程"""
        self._refresh_all()  # 最后一次
        self._stop_flag.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
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
        self._pull_interval()
        self._pull_and_inject_tasks()

        # 收集最新的任务图状态快照，确保推送的数据是最新的
        self.task_graph.collect_runtime_snapshot()

        # 推送逻辑
        self._push_errors()
        self._push_status()
        self._push_structure()
        self._push_analysis()

    # ==== 拉取 ====
    def _pull_interval(self) -> None:
        """从远程服务拉取上报间隔配置"""
        try:
            res = self._session.get(
                f"{self.base_url}/api/pull_interval", timeout=self._pull_timeout()
            )
            if not res.ok:
                raise ReporterError(f"Failed to pull interval: {res.status_code}")

            interval: Any = res.json().get("interval", 5)
            self.interval = int(max(1.0, min(float(interval), 60.0)))
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

            injection_tasks: list[dict[str, Any]] = res.json()
            for injection in injection_tasks:
                target_stage: str | None = injection.get("node")
                task_datas: list[Any] | None = injection.get("task_datas")
                if target_stage is None or task_datas is None:
                    continue

                # 这里你可以按需注入到不同的节点
                task_datas = [
                    task if task != "TERMINATION_SIGNAL" else TERMINATION_SIGNAL
                    for task in task_datas
                ]
                try:
                    self.task_graph.put_stage_queue(  # type: ignore[reportUnknownMemberType]
                        {target_stage: task_datas}, put_termination_signal=False
                    )
                    self.log_inlet.inject_tasks_success(target_stage, task_datas)
                except Exception as e:
                    self.log_inlet.inject_tasks_failed(target_stage, task_datas, e)
        except Exception as e:
            self.log_inlet.pull_tasks_failed(e)

    # ==== 推送 ====
    def _push_errors(self) -> None:
        """推送错误信息"""
        try:
            current_rev = self.task_graph.get_total_error_num()
            jsonl_path = self.task_graph.get_fallback_path()
            resp = {"ok": True, "cached": False}  # 默认响应，避免未定义变量

            # 无新增错误，跳过
            if current_rev == self._last_pushed_errors_rev:
                return

            if self._push_errors_mode == "meta":
                resp = self._push_errors_meta(current_rev, jsonl_path)
                if resp.get("ok"):
                    pass
                elif resp.get("fallback") == "need_content":
                    self._push_errors_mode = "content"
                else:
                    raise ReporterError(f"push_errors_meta failed: {resp.get('msg')}")

            if self._push_errors_mode == "content":
                resp = self._push_errors_content(current_rev, jsonl_path)
                if resp.get("ok"):
                    pass
                else:
                    raise ReporterError(
                        f"push_errors_content failed: {resp.get('msg')}"
                    )

            if resp.get("ok") and not resp.get("cached"):
                self._last_pushed_errors_rev = current_rev

        except Exception as e:
            self.log_inlet.push_errors_failed(e)

    def _push_errors_meta(self, current_rev: int, jsonl_path: str) -> dict[str, Any]:
        """
        推送错误元信息

        :param current_rev: 当前版本号
        :param jsonl_path: 错误日志 JSONL 文件路径
        :return: 服务端响应字典
        """
        payload: dict[str, Any] = {
            "rev": current_rev,
            "jsonl_path": jsonl_path,
        }
        response: requests.Response = self._session.post(
            f"{self.base_url}/api/push_errors_meta",
            json=payload,
            timeout=self._push_timeout(),
        )
        return response.json()

    def _push_errors_content(self, current_rev: int, jsonl_path: str) -> dict[str, Any]:
        """
        推送错误内容（增量：只传 offset 之后的新增条目）

        :param current_rev: 当前版本号
        :param jsonl_path: 错误日志 JSONL 文件路径
        :return: 服务端响应字典
        """
        all_errors: list[dict[str, Any]] = load_jsonl_logs(
            path=jsonl_path,
            keys=["ts", "error_id", "error_repr", "error", "stage", "task_repr"],
        )

        payload: dict[str, Any] = {
            "rev": current_rev,
            "jsonl_path": jsonl_path,
            "errors": all_errors,
        }
        response: requests.Response = self._session.post(
            f"{self.base_url}/api/push_errors_content",
            json=payload,
            timeout=self._push_timeout(),
        )
        return response.json()

    def _push_status(self) -> None:
        """推送状态信息"""
        try:
            payload: dict[str, Any] = self.task_graph.get_status_snapshot()  # type: ignore[reportUnknownMemberType]
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
            structure: list[dict[str, Any]] = self.task_graph.get_structure_json()  # type: ignore[reportUnknownMemberType]
            payload: dict[str, Any] = {"items": structure}
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
            analysis: dict[str, Any] = self.task_graph.get_graph_analysis()  # type: ignore[reportUnknownMemberType]
            payload: dict[str, Any] = {"analysis": analysis}
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
