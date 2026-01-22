import json
import time
import redis
from multiprocessing import Value as MPValue

from .task_stage import TaskStage
from .task_types import TaskEnvelope


class RemoteWorkerError(Exception):
    pass


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

    def init_extra_counter(self):
        self.split_counter = MPValue("i", 0)

    def reset_extra_counter(self):
        self.split_counter.value = 0

    def update_split_counter(self, add_value):
        self.split_counter.value += add_value

    def _split(self, *task):
        """
        实际上这个函数不执行逻辑，仅用于符合 TaskStage 架构
        """
        return task

    def put_split_result(self, result: tuple, task_id: int) -> int:
        split_count = len(result)
        for idx, item in enumerate(result):
            split_id = self.ctree_client.emit(
                "task.split", parents=[task_id], payload={"stage_tag": self.get_tag()}
            )
            splitted_envelope = TaskEnvelope.wrap(item, split_id)
            self.result_queues.put(splitted_envelope)

            self.task_logger.split_trace(
                self.func.__name__,
                idx + 1,
                split_count,
                task_id,
                split_id,
            )

        return split_count

    def process_task_success(self, task_envelope: TaskEnvelope, result, start_time):
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        task = task_envelope.task
        task_hash = task_envelope.hash
        task_id = task_envelope.id

        processed_result = self.process_result(task, result)

        # 清理 retry_time_dict
        self.retry_time_dict.pop(task_hash, None)

        split_count = self.put_split_result(processed_result, task_id)
        self.update_success_counter()
        self.update_split_counter(split_count)

        self.task_logger.split_success(
            self.func.__name__,
            self.get_task_repr(task),
            split_count,
            time.time() - start_time,
        )


class TaskRouter(TaskStage):
    def __init__(self):
        super().__init__(
            func=self._route,
            execution_mode="serial",
            max_retries=0,
        )

    def init_extra_counter(self):
        # 每个 target_tag 一个计数器：用于让不同下游 stage 的 task_counter 统计正确
        self.route_counters: dict = {}

    def reset_extra_counter(self):
        for counter in self.route_counters.values():
            counter.value = 0

    def update_route_counter(self, target: str):
        self.route_counters[target].value += 1

    def _route(self, routed: tuple) -> tuple:
        """
        实际上这个函数不执行逻辑，仅用于符合 TaskStage 架构, 以及提前报错
        """
        if not (isinstance(routed, tuple) and len(routed) == 2):
            raise TypeError(f"TaskRouter expects tuple, got {type(routed).__name__}")
        if routed[0] not in self.route_counters:
            raise ValueError(f"Unknown target: {routed[0]}")
        return routed

    def process_task_success(self, task_envelope: TaskEnvelope, result, start_time):
        """
        统一处理成功任务

        :param task_envelope: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        target, task = task_envelope.task
        task_hash = task_envelope.hash
        task_id = task_envelope.id

        processed_result = self.process_result(task, result)

        # 清理 retry_time_dict
        self.retry_time_dict.pop(task_hash, None)

        route_id = self.ctree_client.emit(
            "task.route", parents=[task_id], payload={"stage_tag": self.get_tag()}
        )
        routed_envelope = TaskEnvelope.wrap(processed_result, route_id)
        self.result_queues.put_target(routed_envelope, target)

        self.update_success_counter()
        self.update_route_counter(target)

        self.task_logger.route_success(
            self.get_func_name(),
            self.get_task_repr(task),
            target,
            time.time() - start_time,
            task_id,
            route_id,
        )


class TaskRedisSink(TaskStage):
    def __init__(
        self,
        key,
        host="localhost",
        port=6379,
        db=0,
        password=None,
        unpack_task_args=False,
    ):
        """
        初始化 TaskRedisSink

        :param key: Redis list key
        :param host: Redis 主机地址
        :param port: Redis 端口
        :param db: Redis 数据库
        :param password: Redis 密码
        :param unpack_task_args: 是否将任务参数解包
        """
        super().__init__(
            func=self._sink,
            execution_mode="thread",
            worker_limit=4,  # 允许 1~2 个线程偶发阻塞，但不会导致整体阻塞
            unpack_task_args=unpack_task_args,
        )
        self.key = key
        self.host = host
        self.port = port
        self.db = db
        self.password = password

    def init_redis(self):
        """初始化 Redis 客户端"""
        if not hasattr(self, "redis_client"):
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )

    def _sink(self, *task):
        self.init_redis()

        task_id = self.get_task_id(task)
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
        key,
        host="localhost",
        port=6379,
        db=0,
        password=None,
        timeout=10,
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

    def init_redis(self):
        if not hasattr(self, "redis_client"):
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )

    def _source(self, *_):
        """
        忽略输入 task，仅作为启动信号
        从 Redis 拉取数据并注入下游
        """
        self.init_redis()

        res = self.redis_client.blpop(self.key, timeout=self._timeout)
        if res is None:
            raise TimeoutError("Redis item not returned in time after being fetched")
        _, item = res
        item_obj: dict = json.loads(item)

        task = item_obj.get("task")
        if len(task) == 1:
            return task[0]

        return tuple(task)


class TaskRedisAck(TaskStage):
    def __init__(
        self,
        key,
        host="localhost",
        port=6379,
        db=0,
        password=None,
        timeout=10,
    ):
        """
        TaskRedisAck: 远端任务完成确认节点（Ack）

        :param key: Redis 结果 key 前缀（通常与 TaskRedisSink 对应）
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

    def init_redis(self):
        if not hasattr(self, "redis_client"):
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )

    def _ack(self, task_id: str):
        """
        接收 task_id，等待远端 worker 的执行结果

        :param task_id: 来自 TaskRedisSink 的 task_id
        :return: 远端执行结果
        """
        self.init_redis()

        start_time = time.time()

        while True:
            result = self.redis_client.hget(self.key, task_id)

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
                    raise ValueError(f"Unknown ack status: {result_obj}")

            # 超时控制
            if self._timeout and (time.time() - start_time) > self._timeout:
                raise TimeoutError(
                    f"TaskRedisAck timeout: task_id={task_id} not acknowledged"
                )

            time.sleep(0.1)
