import json
import time
import redis

from .task_manage import TaskManager


class RemoteWorkerError(Exception):
    pass


class TaskSplitter(TaskManager):
    def __init__(self):
        """
        初始化 TaskSplitter
        """
        super().__init__(
            func=self._split_task,
            execution_mode="serial",
            max_retries=0,
        )

    def _split_task(self, *task):
        """
        实际上这个函数不执行逻辑，仅用于符合 TaskManager 架构
        """
        return task

    def get_args(self, task):
        return task

    def put_split_result(self, result: tuple):
        split_count = 0
        for item in result:
            self.put_result_queues(item)
            split_count += 1

        self.split_output_counter.value += split_count
        return split_count

    def process_result(self, task, result):
        """
        处理不可迭代的任务结果
        """
        if not hasattr(result, "__iter__") or isinstance(result, (str, bytes)):
            result = (result,)
        elif isinstance(result, list):
            result = tuple(result)

        return result

    def process_task_success(self, task, result, start_time):
        """
        统一处理成功任务

        :param task: 完成的任务
        :param result: 任务的结果
        :param start_time: 任务开始时间
        """
        processed_result = self.process_result(task, result)

        if self.enable_result_cache:
            self.success_dict[task] = processed_result

        # ✅ 清理 retry_time_dict
        task_id = self.get_task_id(task)
        self.retry_time_dict.pop(task_id, None)

        split_count = self.put_split_result(result)
        self.update_success_counter()

        self.task_logger.splitter_success(
            self.func.__name__,
            self.get_task_info(task),
            split_count,
            time.time() - start_time,
        )


class TaskRedisTransfer(TaskManager):
    def __init__(
        self,
        worker_limit=50,
        unpack_task_args=False,
        host="localhost",
        port=6379,
        db=0,
        fetch_timeout=10,
        result_timeout=10,
    ):
        """
        初始化 TaskRedisTransfer
        
        :param worker_limit: 并行工作线程数
        :param unpack_task_args: 是否将任务参数解包
        :param host: Redis 主机地址
        :param port: Redis 端口
        :param db: Redis 数据库
        :param fetch_timeout: Redis 任务等待超时时间
        :param result_timeout: Redis 结果等待超时时间
        """
        super().__init__(
            func=self._trans_redis,
            execution_mode="thread",
            worker_limit=worker_limit,
            unpack_task_args=unpack_task_args,
        )

        self.host = host
        self.port = port
        self.db = db
        self.fetch_timeout = fetch_timeout
        self.result_timeout = result_timeout

    def init_redis(self):
        """初始化 Redis 客户端"""
        if not hasattr(self, "redis_client"):
            self.redis_client = redis.Redis(
                host=self.host, port=self.port, db=self.db, decode_responses=True
            )

    def _trans_redis(self, *task):
        """
        将任务写入 Redis, 并等待结果
        """
        self.init_redis()
        input_key = f"{self.get_stage_tag()}:input"
        output_key = f"{self.get_stage_tag()}:output"

        # 提交任务
        task_id = self.get_task_id(task)
        payload = json.dumps({"id": task_id, "task": task})
        self.redis_client.rpush(input_key, payload)

        # ✅ 等待任务被 BLPOP 拿走（不在 list 中）
        wait_start = time.time()
        while True:
            if self.redis_client.lpos(input_key, payload) is None:  # 已被取走
                break
            if time.time() - wait_start > self.fetch_timeout:
                raise TimeoutError("Task not fetched from Redis in time")
            time.sleep(0.1)

        # ✅ 被取走后再进入结果等待阶段
        start_time = time.time()
        while True:
            result = self.redis_client.hget(output_key, task_id)
            if result:
                self.redis_client.hdel(output_key, task_id)
                result_obj = json.loads(result)
                if result_obj.get("status") == "success":
                    return result_obj.get("result")
                elif result_obj.get("status") == "error":
                    raise RemoteWorkerError(f"{result_obj.get('error')}")
                else:
                    raise ValueError(f"Unknown result status: {result_obj}")
            if time.time() - start_time > self.result_timeout:
                raise TimeoutError(
                    "Redis result not returned in time after being fetched"
                )
            time.sleep(0.1)
