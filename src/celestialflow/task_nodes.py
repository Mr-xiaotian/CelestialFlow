import json
import time
import redis

from .task_manage import TaskManager
from .task_tools import object_to_str_hash


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
    
    def put_split_result(self, result):
        split_count = 0
        for item in result:
            self.put_result_queues(item)
            split_count += 1

        self.extra_stats["split_output_count"].value += split_count
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
        self.success_dict[task] = processed_result

        self.update_succes_counter()
        split_count = self.put_split_result(result)

        self.task_logger.splitter_success(
            self.func.__name__,
            self.get_task_info(task),
            split_count,
            time.time() - start_time,
        )


class TaskRedisTransfer(TaskManager):
    def __init__(self, worker_limit=50, unpack_task_args=False, host="localhost", port=6379, db=0, timeout=10):
        """
        初始化 TaskRedisTransfer
        :param worker_limit: 并行工作线程数
        :param unpack_task_args: 是否将任务参数解包
        :param host: Redis 主机地址
        :param port: Redis 端口
        :param db: Redis 数据库
        :param timeout: Redis 操作超时时间
        """
        super().__init__(
            func=self._trans_redis, 
            execution_mode="thread", 
            worker_limit=worker_limit, 
            unpack_task_args=unpack_task_args
        )

        self.host = host
        self.port = port
        self.db = db
        self.timeout = timeout

    def init_redis(self):
        """初始化 Redis 客户端"""
        if not hasattr(self, "redis_client"):
            self.redis_client = redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True)

    def _trans_redis(self, *task):
        """
        将任务写入 Redis, 并等待结果
        """
        self.init_redis()
        input_key = f"{self.get_stage_tag()}:input"
        output_key = f"{self.get_stage_tag()}:output"

        # 将任务写入 redis（如 list 或 stream）
        task_id = object_to_str_hash(task)
        payload = json.dumps({"id": task_id, "task": task})
        self.redis_client.rpush(input_key, payload)

        # 等待结果（可以阻塞，或轮询）
        start_time = time.time()
        while True:
            result = self.redis_client.hget(output_key, task_id)
            if result:
                self.redis_client.hdel(output_key, task_id)
                try:
                    result_obj = json.loads(result)
                except Exception as e:
                    raise ValueError(f"Invalid JSON from Redis: {result!r}") from e

                if result_obj.get("status") == "success":
                    return result_obj.get("result")
                elif result_obj.get("status") == "error":
                    raise RuntimeError(f"Remote worker error: {result_obj.get('error')}")
                else:
                    raise ValueError(f"Unknown result status: {result_obj}")
            elif time.time() - start_time > self.timeout:
                raise TimeoutError("Redis result not returned in time")
            time.sleep(0.1)
