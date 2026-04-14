# stage/core_stages.py
import json
import time
from multiprocessing import Value as MPValue
from typing import Any, cast

import redis

from ..runtime import TaskEnvelope
from ..runtime.util_errors import InvalidOptionError, RemoteWorkerError
from .core_stage import TaskStage


class TaskSplitter(TaskStage):
    def __init__(self):
        """
        初始化 TaskSplitter
        """
        super().__init__(
            func=self._split,
            execution_mode="serial",
            max_retries=0,
            unpack_task_args=True,
        )

        self.init_extra_counter()

    def init_extra_counter(self) -> None:
        """初始化额外的计数器"""
        self.split_counter = MPValue("i", 0)

    def reset_extra_counter(self) -> None:
        """重置额外的计数器"""
        self.split_counter.value = 0

    def update_split_counter(self, add_value: int) -> None:
        """更新 split 计数器"""
        self.split_counter.value += add_value

    def _split(self, *task: Any) -> tuple:
        """
        这个函数不执行逻辑，仅用于符合 TaskStage 架构
        """
        return task

    def put_split_result(self, result: tuple, task_id: int) -> int:
        """
        将 split 结果放入队列，并发出对应事件

        :param result: split 的结果，必须是一个可迭代对象
        :param task_id: 原始任务 ID，用于事件关联
        :return: split 的子任务数量
        """
        result_queues = self.result_queues

        split_count = len(result)
        for idx, item in enumerate(result):
            split_id = self.ctree_client.emit(
                "task.split",
                parents=[task_id],
                payload=self.get_summary(),
            )
            splitted_envelope = TaskEnvelope.wrap(
                item,
                split_id,
                source=self.get_tag(),
            )
            result_queues.put(splitted_envelope)

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
        task, task_hash, task_id, _ = task_envelope.unwrap()

        processed_result = self.process_result(task, result)

        self.metrics.retry_time_dict.pop(task_hash, None)

        split_count = self.put_split_result(processed_result, task_id)
        self.metrics.add_success_count()
        self.update_split_counter(split_count)

        self.log_inlet.split_success(
            self.get_func_name(),
            self.get_task_repr(task),
            split_count,
            time.perf_counter() - start_time,
        )


class TaskRouter(TaskStage):
    def __init__(self):
        """初始化 TaskRouter"""
        super().__init__(
            func=self._route,
            execution_mode="serial",
            max_retries=0,
        )

        self.init_extra_counter()

    def init_extra_counter(self) -> None:
        """初始化额外的计数器"""
        # 每个 target_tag 一个计数器：用于让不同下游 stage 的 task_counter 统计正确
        self.route_counters: dict[str, Any] = {}

    def reset_extra_counter(self) -> None:
        """重置额外的计数器"""
        for counter in self.route_counters.values():
            counter.value = 0

    def update_route_counter(self, target: str) -> None:
        """更新 route 计数器"""
        self.route_counters[target].value += 1

    def _route(self, routed: tuple) -> Any:
        """
        这个函数仅用于提前报错
        """
        if not (isinstance(routed, tuple) and len(routed) == 2):
            raise TypeError(f"TaskRouter expects tuple, got {type(routed).__name__}")
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
        (target, task), task_hash, task_id, _ = task_envelope.unwrap()

        processed_result = self.process_result(task, result)

        self.metrics.retry_time_dict.pop(task_hash, None)

        route_id = self.ctree_client.emit(
            "task.route",
            parents=[task_id],
            payload=self.get_summary(),
        )
        routed_envelope = TaskEnvelope.wrap(
            processed_result,
            route_id,
            source=self.get_tag(),
        )
        result_queues = self.result_queues

        result_queues.put_target(routed_envelope, target)

        self.metrics.add_success_count()
        self.update_route_counter(target)

        self.log_inlet.route_success(
            self.get_func_name(),
            self.get_task_repr(task),
            target,
            time.perf_counter() - start_time,
            task_id,
            route_id,
        )


class TaskRedisTransport(TaskStage):
    def __init__(
        self,
        key: str,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        unpack_task_args: bool = False,
    ):
        """
        初始化 TaskRedisTransport

        :param key: Redis list key
        :param host: Redis 主机地址
        :param port: Redis 端口
        :param db: Redis 数据库
        :param password: Redis 密码
        :param unpack_task_args: 是否将任务参数解包
        """
        super().__init__(
            func=self._transport,
            execution_mode="thread",
            max_workers=4,  # 允许 1~2 个线程偶发阻塞，但不会导致整体阻塞
            unpack_task_args=unpack_task_args,
        )
        self.key = key
        self.host = host
        self.port = port
        self.db = db
        self.password = password

    def init_redis(self) -> None:
        """初始化 Redis 客户端"""
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
        将任务元组转换为 JSON 字符串并写入 Redis list

        :param task: 任务元组
        :return: 任务 ID
        """
        self.init_redis()

        task_id = id(task)
        payload = json.dumps(
            {
                "id": task_id,
                "task": task,
                "emit_ts": time.time(),
            }
        )
        self.redis_client.rpush(self.key, payload)

        return task_id


class TaskRedisSource(TaskStage):
    def __init__(
        self,
        key: str,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        timeout: int = 10,
    ):
        """
        初始化 TaskRedisSource

        :param key: Redis list key
        :param host: Redis 主机地址
        :param port: Redis 端口
        :param db: Redis 数据库
        :param password: Redis 密码
        :param timeout: Redis 超时时间, 设为0则无限等待
        """
        super().__init__(
            func=self._source,
            execution_mode="serial",  # source 本身不需要并行
            enable_duplicate_check=False,
        )
        self.key = key
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._timeout = timeout

    def init_redis(self) -> None:
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
        忽略输入 task，仅作为启动信号
        从 Redis 拉取数据并注入下游
        """
        self.init_redis()

        res = cast(Any, self.redis_client.blpop(self.key, timeout=self._timeout))
        if res is None:
            raise TimeoutError("Redis item not returned in time after being fetched")
        _, item = res
        item = cast(str, item)
        item_obj: dict = json.loads(item)

        task = item_obj.get("task")
        if task is None:
            raise RemoteWorkerError("Redis source payload missing 'task'")
        if len(task) == 1:
            return task[0]

        return tuple(task)


class TaskRedisAck(TaskStage):
    def __init__(
        self,
        key: str,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        timeout: int = 10,
    ):
        """
        TaskRedisAck: 远端任务完成确认节点（Ack）

        :param key: Redis 结果 key 前缀（通常与 TaskRedisTransport 对应）
        :param host: Redis 主机地址
        :param port: Redis 端口
        :param db: Redis 数据库
        :param password: Redis 密码
        :param timeout: 等待结果的超时时间（秒），0 表示无限等待
        """
        super().__init__(
            func=self._ack,
            execution_mode="serial",  # Ack 是顺序语义
            enable_duplicate_check=False,  # task_id 天然唯一
        )

        self.key = key
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._timeout = timeout

    def init_redis(self) -> None:
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
        """
        self.init_redis()

        start_time = time.perf_counter()

        while True:
            result = cast(str | None, self.redis_client.hget(self.key, task_id))

            if result:
                # 取到结果即删除，保证 Ack 语义一次性
                self.redis_client.hdel(self.key, task_id)

                result_obj: dict = json.loads(result)
                status = result_obj.get("status")

                if status == "success":
                    result = result_obj.get("result")
                    if not hasattr(result, "__iter__") or isinstance(
                        result, (str, bytes)
                    ):
                        return result
                    elif isinstance(result, list):
                        if len(result) == 1:
                            return result[0]
                        return tuple(result)
                    else:
                        return result

                elif status == "error":
                    raise RemoteWorkerError(result_obj.get("error"))

                else:
                    raise RemoteWorkerError(f"Unknown ack status: {result_obj}")

            # 超时控制
            if self._timeout and (time.perf_counter() - start_time) > self._timeout:
                raise TimeoutError(
                    f"TaskRedisAck timeout: task_id={task_id} not acknowledged"
                )

            time.sleep(0.1)
