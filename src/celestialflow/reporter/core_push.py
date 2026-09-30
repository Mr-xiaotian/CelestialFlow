# reporter/core_push.py
from __future__ import annotations

import time
import traceback
from threading import Event, Lock, Thread
from typing import Any

import requests

from ..funnel import BaseInlet, BaseSpout
from ..observer import Observer, TaskFailEvent
from ..persist.util_payload import to_persisted_payload
from ..runtime.util_errors import ReporterError


def to_error_record(event: TaskFailEvent) -> dict[str, Any]:
    """
    将任务失败事件转换为服务端接受的上报记录。

    ``event_id`` 采用失败事件自身的事件 ID，以便服务端按 ``event_id`` 幂等去重。

    :param event: 任务失败事件
    :return: 上报记录字典
    """
    return {
        "event_id": event.error_id,
        "node": event.node,
        "status": "failed",
        "error_type": type(event.exception).__name__,
        "error_message": str(event.exception),
        "ts": time.time(),
        "task_json": to_persisted_payload(event.task),
        "result_json": None,
    }


class PushSpout(BaseSpout):
    """
    在后台线程中把上报记录批量推送到远程服务的推送通道。

    当前只承载失败记录（``/api/push_errors``）；后续会在此基础上承载错误状态等
    更多上报内容，因此命名不绑定具体载荷。记录先进入内部缓冲，满足以下任一条件时
    合并为一次请求推送：

    - 缓冲记录数达到 ``batch_size``（在消费线程上同步冲刷）；
    - 距上一条记录超过 ``flush_interval`` 秒（由独立 flush 线程定时冲刷）。

    ``stop()`` 收尾时会冲刷剩余记录，保证不丢尾部。单批推送失败不会中断线程
    （异常被捕获并打印），该批记录会被丢弃。
    """

    def __init__(
        self,
        graph_id: str,
        base_url: str,
        timeout: float = 3.0,
        *,
        batch_size: int = 20,
        flush_interval: float = 2.0,
    ) -> None:
        """
        初始化推送监听器。

        :param graph_id: 上报会话标识，随记录一并提交给服务端
        :param base_url: 远程服务基础地址
        :param timeout: 单次推送请求的超时时间（秒），默认 3.0
        :param batch_size: 触发立即冲刷的缓冲记录数上限，默认 20
        :param flush_interval: 定时冲刷窗口（秒），默认 2.0；``<= 0`` 时关闭定时冲刷
        """
        super().__init__()
        self.graph_id = graph_id
        self.base_url = base_url
        self.timeout = timeout
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        self._session: requests.Session | None = None
        self._buffer: list[dict[str, Any]] = []
        self._buffer_lock = Lock()
        self._send_lock = Lock()
        self._stop_flush = Event()
        self._flush_thread: Thread | None = None

    # ==== 生命周期回调 ====

    def _before_start(self) -> None:
        """创建复用的 HTTP 会话，并启动定时冲刷线程。"""
        self._session = requests.Session()
        self._buffer = []
        self._stop_flush.clear()
        if self.flush_interval > 0:
            self._flush_thread = Thread(target=self._flush_loop, daemon=True)
            self._flush_thread.start()

    def _after_stop(self) -> None:
        """停止定时冲刷线程、冲刷剩余记录并关闭 HTTP 会话。"""
        self._stop_flush.set()
        if self._flush_thread is not None:
            self._flush_thread.join(timeout=5)
            self._flush_thread = None
        self._flush()
        if self._session is not None:
            self._session.close()
            self._session = None

    # ==== 处理 ====

    def _handle_record(self, record: dict[str, Any]) -> None:
        """
        缓存单条记录，缓冲满时立即合并冲刷。

        :param record: 队列中取出的记录
        """
        with self._buffer_lock:
            self._buffer.append(record)
            full = len(self._buffer) >= self.batch_size
        if full:
            self._flush()

    def _flush_loop(self) -> None:
        """定时冲刷循环：每个窗口唤醒一次，或在收到停止信号时退出。"""
        while not self._stop_flush.wait(self.flush_interval):
            self._flush()

    def _flush(self) -> None:
        """取走缓冲记录并合并为一次请求推送；失败时打印且不向外抛出。"""
        with self._buffer_lock:
            if not self._buffer or self._session is None:
                return
            batch = self._buffer
            self._buffer = []
        with self._send_lock:
            try:
                self._post(batch)
            except Exception:
                # 单批推送失败不致死线程。
                traceback.print_exc()

    def _post(self, batch: list[dict[str, Any]]) -> None:
        """
        将一批记录推送到 ``/api/push_errors``。

        :param batch: 待推送的记录列表
        :raises ReporterError: 服务端返回非 2xx 时
        """
        session = self._session
        if session is None:
            return
        res = session.post(
            f"{self.base_url}/api/push_errors",
            json={"graph_id": self.graph_id, "errors": batch},
            timeout=self.timeout,
        )
        if not res.ok:
            raise ReporterError(f"Failed to push errors: {res.status_code}")


class NullPushSpout(BaseSpout):
    """空实现的推送监听器，用于关闭上报时的占位对象。

    消费到的记录会被直接丢弃，不建立任何 HTTP 会话，也不上报。
    """

    def _handle_record(self, _record: Any) -> None:
        """
        丢弃记录，不做任何上报。

        :param _record: 队列中取出的记录
        """
        return None


class PushInlet(BaseInlet, Observer):
    """
    推送观察者：把观测到的任务事件转换为上报记录并入队，交由推送 spout 发送。

    当前仅处理 :meth:`on_task_fail`；后续承载更多上报内容时在此按事件分派。
    """

    def on_task_fail(self, event: TaskFailEvent) -> None:
        """
        将任务失败事件转换为上报记录并入队。

        :param event: 任务失败事件
        """
        self._funnel(to_error_record(event))
