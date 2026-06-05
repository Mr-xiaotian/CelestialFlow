# stage/core_stages.py
import json
import time
from typing import Any, cast

import redis

from ..runtime import TaskEnvelope
from ..runtime.util_errors import (
    CelestialFlowTimeoutError,
    InvalidOptionError,
    RemoteWorkerError,
    TaskFormatError,
)
from ..runtime.util_types import ValueWrapper
from .core_stage import TaskStage


# ==== TaskSplitter ====
class TaskSplitter(TaskStage):
    """TaskSplitter: 将单个任务拆分为多个子任务，注入下游队列。"""

    split_counter: ValueWrapper
    execution_mode: str

    def __init__(self, name: str, stage_mode: str = "serial"):
        """
        初始化 TaskSplitter

        :param name: 节点名称
        :param stage_mode: 节点运行模式，默认 'serial'
        """
        super().__init__(
            name=name,
            func=self._split,
            stage_mode=stage_mode,
            execution_mode="serial",
            max_retries=0,
            unpack_task_args=True,
        )

        self._init_extra_counter()

    def _init_extra_counter(self) -> None:
        """初始化 split 计数器，用于跟踪 split 产生的子任务总数"""
        self.split_counter = ValueWrapper(0)

    def set_execution_mode(self, execution_mode: str) -> None:
        """覆写父类方法，将执行模式固定为串行"""
        self.execution_mode = "serial"

    def get_binding_counter(self, _downstream_name: str) -> Any:
        """
        返回下游 stage 应绑定的计数器

        :param _downstream_name: 下游 stage 的唯一名称
        :return: split 计数器实例
        """
        return self.split_counter

    def _update_split_counter(self, add_value: int) -> None:
        """
        更新 split 计数器

        :param add_value: 增加的子任务数量
        """
        self.split_counter.value += add_value

    def _split(self, *task: Any) -> tuple[Any, ...]:
        """
        透传任务参数，仅用于符合 TaskStage 架构

        :param task: 任务参数
        :return: 原样返回的任务元组
        """
        return task

    def _put_split_result(self, result: tuple[Any, ...], task_id: int) -> int:
        """
        将 split 结果放入队列，并发出对应事件

        :param result: split 的结果，必须是一个可迭代对象
        :param task_id: 原始任务 ID，用于事件关联
        :return: split 的子任务数量
        """
        result_queue = self.result_queue

        split_count = len(result)
        for idx, item in enumerate(result):
            split_id = self.ctree_client.emit(
                "task.split",
                parents=[task_id],
                payload=self.get_summary(),
            )
            splitted_envelope = TaskEnvelope(
                item,
                split_id,
                source=self.get_name(),
            )
            result_queue.put(splitted_envelope)

            self.log_inlet.split_trace(
                self.get_func_name(),
                idx + 1,
                split_count,
                task_id,
                split_id,
            )

        return split_count

    def process_task_success(
        self, task_envelope: TaskEnvelope, result: Any, start_time: float
    ) -> None:
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        processed_result = self.process_result(task, result)

        split_count = self._put_split_result(processed_result, task_id)
        self.metrics.add_success_count()
        self._update_split_counter(split_count)

        self.log_inlet.split_success(
            self.get_func_name(),
            self.get_task_repr(task),
            split_count,
            time.perf_counter() - start_time,
        )


# ==== TaskRouter ====
class TaskRouter(TaskStage):
    """TaskRouter: 根据路由信息将任务分发到不同的下游 stage。"""

    route_counters: dict[str, ValueWrapper]

    def __init__(self, name: str, stage_mode: str = "serial"):
        """
        初始化 TaskRouter

        :param name: 节点名称
        :param stage_mode: 节点运行模式，默认 'serial'
        """
        super().__init__(
            name=name,
            func=self._route,
            stage_mode=stage_mode,
            execution_mode="serial",
            max_retries=0,
        )

        self._init_extra_counter()

    def _init_extra_counter(self) -> None:
        """
        初始化路由计数器

        每个 target_name 一个计数器，用于让不同下游 stage 的 task_counter 统计正确。
        """
        self.route_counters = {}

    def get_binding_counter(self, downstream_name: str) -> Any:
        """
        返回下游 stage 应绑定的计数器，按唯一名称查找或创建

        :param downstream_name: 下游 stage 的唯一名称
        :return: 对应下游的路由计数器实例
        """
        self.route_counters.setdefault(downstream_name, ValueWrapper(0))
        return self.route_counters[downstream_name]

    def _update_route_counter(self, target: str) -> None:
        """
        更新指定目标的路由计数器

        :param target: 目标 stage 的唯一名称
        """
        self.route_counters[target].value += 1

    def _route(self, routed: tuple[str, Any]) -> Any:
        """
        校验路由输入格式并提取目标任务

        :param routed: (target_name, task) 元组
        :return: 提取出的任务数据
        :raises TypeError: 输入不是长度为 2 的元组
        :raises InvalidOptionError: target 不在已注册的路由列表中
        """
        if not (isinstance(routed, tuple) and len(routed) == 2):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TaskFormatError(
                f"TaskRouter expects tuple, got {type(routed).__name__}"
            )
        target, task = routed
        if target not in self.route_counters:
            raise InvalidOptionError(
                "Unknown target", target, self.route_counters.keys()
            )
        return task

    def process_task_success(
        self, task_envelope: TaskEnvelope, result: Any, start_time: float
    ) -> None:
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        (target, task) = task_envelope.get_task()
        task_id = task_envelope.get_id()

        processed_result = self.process_result(task, result)

        route_id = self.ctree_client.emit(
            "task.route",
            parents=[task_id],
            payload=self.get_summary(),
        )
        routed_envelope = TaskEnvelope(
            processed_result,
            route_id,
            source=self.get_name(),
        )
        result_queue = self.result_queue

        result_queue.put_target(routed_envelope, target)

        self.metrics.add_success_count()
        self._update_route_counter(target)

        self.log_inlet.route_success(
            self.get_func_name(),
            self.get_task_repr(task),
            target,
            time.perf_counter() - start_time,
            task_id,
            route_id,
        )


# ==== TaskRedisTransport ====
class TaskRedisTransport(TaskStage):
    """Redis 任务传输节点，将任务序列化后写入 Redis list。"""

    key: str
    host: str
    port: int
    db: int
    password: str | None
    redis_client: "redis.Redis"

    def __init__(
        self,
        name: str,
        key: str = "",
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        stage_mode: str = "serial",
        unpack_task_args: bool = False,
    ):
        """
        初始化 TaskRedisTransport

        :param name: 节点名称
        :param key: Redis list key，默认 ""
        :param host: Redis 主机地址，默认 "localhost"
        :param port: Redis 端口，默认 6379
        :param db: Redis 数据库，默认 0
        :param password: Redis 密码，默认 None
        :param stage_mode: 节点运行模式，默认 "serial"
        :param unpack_task_args: 是否将任务参数解包，默认 False
        """
        super().__init__(
            name=name,
            func=self._transport,
            stage_mode=stage_mode,
            execution_mode="thread",
            max_workers=4,
            unpack_task_args=unpack_task_args,
        )
        self.key = key
        self.host = host
        self.port = port
        self.db = db
        self.password = password

        self.task_id_counter = 0

    def init_redis(self) -> None:
        """初始化 Redis 客户端（惰性，仅首次调用时创建连接）"""
        if not hasattr(self, "redis_client"):
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )

    def _transport(self, *task: Any) -> int:
        """
        将任务元组序列化为 JSON 并写入 Redis list

        :param task: 任务参数元组
        :return: 任务 ID
        """
        self.init_redis()

        task_id = self.task_id_counter
        self.task_id_counter += 1
        payload = json.dumps(
            {
                "id": task_id,
                "task": task,
                "emit_ts": time.time(),
            }
        )
        self.redis_client.rpush(self.key, payload)

        return task_id


# ==== TaskRedisSource ====
class TaskRedisSource(TaskStage):
    """Redis 任务源节点，从 Redis list 拉取数据并注入下游。"""

    key: str
    host: str
    port: int
    db: int
    password: str | None
    timeout: int
    redis_client: "redis.Redis"

    def __init__(
        self,
        name: str,
        key: str = "",
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        timeout: int = 10,
        stage_mode: str = "serial",
    ):
        """
        初始化 TaskRedisSource

        :param name: 节点名称
        :param key: Redis list key，默认 ""
        :param host: Redis 主机地址，默认 "localhost"
        :param port: Redis 端口，默认 6379
        :param db: Redis 数据库，默认 0
        :param password: Redis 密码，默认 None
        :param timeout: Redis 超时时间, 设为0则无限等待，默认 10
        :param stage_mode: 节点运行模式，默认 "serial"
        """
        super().__init__(
            name=name,
            func=self._source,
            stage_mode=stage_mode,
            execution_mode="serial",
            enable_duplicate_check=False,
        )
        self.key = key
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.timeout = timeout

    def init_redis(self) -> None:
        """初始化 Redis 客户端（惰性，仅首次调用时创建连接）"""
        if not hasattr(self, "redis_client"):
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )

    def _source(self, *_: Any) -> Any:
        """
        从 Redis list 拉取数据并注入下游，忽略输入任务

        :param _: 忽略的输入参数（仅作为启动信号）
        :return: 从 Redis 拉取的任务数据
        :raises CelestialFlowTimeoutError: 超时未获取到数据
        :raises RemoteWorkerError: 返回的 payload 中缺少 'task' 字段
        """
        self.init_redis()

        redis_client = cast(Any, self.redis_client)
        res = cast(list[Any] | None, redis_client.blpop(self.key, timeout=self.timeout))
        if res is None:
            raise CelestialFlowTimeoutError(
                "Redis item not returned in time after being fetched"
            )
        _, item = res
        item = cast(str, item)
        item_obj: dict[str, Any] = json.loads(item)

        task: Any = item_obj.get("task")
        if task is None:
            raise RemoteWorkerError("Redis source payload missing 'task'")
        if len(task) == 1:
            return task[0]

        return tuple(task)


# ==== TaskRedisAck ====
class TaskRedisAck(TaskStage):
    """Redis 任务确认节点，等待远端 Worker 返回执行结果。"""

    key: str
    host: str
    port: int
    db: int
    password: str | None
    timeout: int
    redis_client: "redis.Redis"

    def __init__(
        self,
        name: str,
        key: str = "",
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        timeout: int = 10,
        stage_mode: str = "serial",
    ):
        """
        TaskRedisAck: 远端任务完成确认节点（Ack）

        :param name: 节点名称
        :param key: Redis 结果 key 前缀（通常与 TaskRedisTransport 对应），默认 ""
        :param host: Redis 主机地址，默认 "localhost"
        :param port: Redis 端口，默认 6379
        :param db: Redis 数据库，默认 0
        :param password: Redis 密码，默认 None
        :param timeout: 等待结果的超时时间（秒），0 表示无限等待，默认 10
        :param stage_mode: 节点运行模式，默认 "serial"
        """
        super().__init__(
            name=name,
            func=self._ack,
            stage_mode=stage_mode,
            execution_mode="serial",  # Ack 是顺序语义
            enable_duplicate_check=False,  # task_id 天然唯一
        )

        self.key = key
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.timeout = timeout

    def init_redis(self) -> None:
        """初始化 Redis 客户端（惰性，仅首次调用时创建连接）"""
        if not hasattr(self, "redis_client"):
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )

    def _ack(self, task_id: str) -> Any:
        """
        接收 task_id，等待远端 worker 的执行结果

        :param task_id: 来自 TaskRedisTransport 的 task_id
        :return: 远端执行结果
        :raises RemoteWorkerError: 远端 worker 返回错误状态或未知状态
        :raises CelestialFlowTimeoutError: 等待远端结果超时
        """
        self.init_redis()

        start_time = time.perf_counter()

        while True:
            result = cast(str | None, self.redis_client.hget(self.key, task_id))

            if result:
                # 取到结果即删除，保证 Ack 语义一次性
                self.redis_client.hdel(self.key, task_id)

                result_obj: dict[str, Any] = json.loads(result)
                status = result_obj.get("status")

                if status == "success":
                    result: Any = result_obj.get("result")
                    if not hasattr(result, "__iter__") or isinstance(
                        result, str | bytes
                    ):
                        return result
                    elif isinstance(result, list):
                        if len(result) == 1:  # pyright: ignore[reportUnknownArgumentType]
                            return result[0]  # pyright: ignore[reportUnknownVariableType]
                        return tuple(result)  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
                    else:
                        return result

                elif status == "error":
                    raise RemoteWorkerError(result_obj.get("error"))

                else:
                    raise RemoteWorkerError(f"Unknown ack status: {result_obj}")

            # 超时控制
            if self.timeout and (time.perf_counter() - start_time) > self.timeout:
                raise CelestialFlowTimeoutError(
                    f"TaskRedisAck timeout: task_id={task_id} not acknowledged"
                )

            time.sleep(0.1)
