from threading import Event, Thread

import requests

from .task_logging import TaskLogger
from .task_types import TERMINATION_SIGNAL


class TaskReporter:
    """
    周期性向远程服务推送任务运行状态的上报器。

    - 定时从服务器拉取配置（如上报间隔、任务注入信息）
    - 将任务图中的状态、错误、结构、拓扑等信息推送到后端接口
    - 以后台线程方式运行，可随时 start()/stop()
    - 主要用于可视化监控、任务远程控制与 Web UI 同步
    """

    def __init__(self, task_graph, log_queue, log_level, host="127.0.0.1", port=5000):
        from .task_graph import TaskGraph

        self.task_graph: TaskGraph = task_graph
        self.logger = TaskLogger(log_queue, log_level)
        self.base_url = f"http://{host}:{port}"
        self._stop_flag = Event()
        self._thread = None
        self.interval = 5

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop_flag.clear()
            self._thread = Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        if self._thread:
            self._refresh_all()  # 最后一次
            self._stop_flag.set()
            self._thread.join(timeout=2)
            self._thread = None
            self.logger.stop_reporter()

    def _loop(self):
        while not self._stop_flag.is_set():
            try:
                self._refresh_all()
            except Exception as e:
                self.logger.loop_failed(e)
            self._stop_flag.wait(self.interval)

    def _refresh_all(self):
        # 拉取逻辑
        self._pull_interval()
        self._pull_and_inject_tasks()

        # 推送逻辑
        self._push_errors_meta()
        self._push_status()
        self._push_structure()
        self._push_topology()

    def _pull_interval(self):
        try:
            res = requests.get(f"{self.base_url}/api/get_interval", timeout=1)
            if res.ok:
                interval = res.json().get("interval", 5)
                self.interval = max(1.0, min(interval, 60.0))
        except Exception as e:
            self.logger.pull_interval_failed(e)

    def _pull_and_inject_tasks(self):
        try:
            res = requests.get(f"{self.base_url}/api/get_task_injection", timeout=2)
            if res.ok:
                tasks_list = res.json()
                for task in tasks_list:
                    target_node = task.get("node")
                    task_datas = task.get("task_datas")

                    # 这里你可以按需注入到不同的节点
                    task_datas = [
                        task if task != "TERMINATION_SIGNAL" else TERMINATION_SIGNAL
                        for task in task_datas
                    ]
                    try:
                        self.task_graph.put_stage_queue(
                            {target_node: task_datas}, put_termination_signal=False
                        )
                        self.logger.inject_tasks_success(target_node, task_datas)
                    except Exception as e:
                        self.logger.inject_tasks_failed(target_node, task_datas, e)
        except Exception as e:
            self.logger.pull_tasks_failed(e)

    def _push_errors_meta(self):
        try:
            self.task_graph.handle_fail_queue()
            payload = {"jsonl_path": self.task_graph.get_error_jsonl_path(), "rev": self.task_graph.total_error_num}
            requests.post(f"{self.base_url}/api/push_errors_meta", json=payload, timeout=1)
        except Exception as e:
            self.logger.push_errors_failed(e)

    def _push_status(self):
        try:
            status_data = self.task_graph.get_status_dict()
            payload = {"status": status_data}
            requests.post(f"{self.base_url}/api/push_status", json=payload, timeout=1)
        except Exception as e:
            self.logger.push_status_failed(e)

    def _push_structure(self):
        try:
            structure = self.task_graph.get_structure_json()
            payload = {"items": structure}
            requests.post(
                f"{self.base_url}/api/push_structure", json=payload, timeout=1
            )
        except Exception as e:
            self.logger.push_structure_failed(e)

    def _push_topology(self):
        try:
            topology = self.task_graph.get_graph_topology()
            payload = {"topology": topology}
            requests.post(f"{self.base_url}/api/push_topology", json=payload, timeout=1)
        except Exception as e:
            self.logger.push_topology_failed(e)


class NullTaskReporter:
    interval = 0

    def start():
        return None

    def stop():
        return None
