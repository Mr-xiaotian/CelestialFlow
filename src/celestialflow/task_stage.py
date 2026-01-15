from __future__ import annotations

import time
from typing import List
from multiprocessing import Value as MPValue
from multiprocessing import Queue as MPQueue

from .task_manage import TaskManager
from .task_queue import TaskQueue
from .task_types import TERMINATION_SIGNAL


class TaskStage(TaskManager):
    _name = "Stage"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.next_stages: List[TaskStage] = []
        self.prev_stages: List[TaskStage] = []
        self._pending_prev_bindings = []

    def set_graph_context(
        self,
        next_stages: List[TaskStage] = None,
        stage_mode: str = None,
        stage_name: str = None,
    ):
        """
        设置链式上下文(仅限组成graph时)

        :param next_stages: 后续节点列表
        :param stage_mode: 当前节点执行模式, 可以是 'serial'（串行）或 'process'（并行）
        :param name: 当前节点名称
        """
        self.set_next_stages(next_stages)
        self.set_stage_mode(stage_mode)
        self.set_stage_name(stage_name)
        self._finalize_prev_bindings()

    def set_next_stages(self, next_stages: List[TaskStage]):
        """
        设置后续节点列表, 并为后续节点添加本节点为前置节点

        :param next_stages: 后续节点列表
        """
        self.next_stages = next_stages or []
        for next_stage in self.next_stages:
            next_stage.add_prev_stages(self)

    def set_stage_mode(self, stage_mode: str):
        """
        设置当前节点在graph中的执行模式, 可以是 'serial'（串行）或 'process'（并行）

        :param stage_mode: 当前节点执行模式
        """
        self.stage_mode = stage_mode if stage_mode == "process" else "serial"

    def add_prev_stages(self, prev_stage: TaskStage):
        """
        添加前置节点

        :param prev_stage: 前置节点
        """
        from .task_nodes import TaskSplitter, TaskRouter

        if prev_stage in self.prev_stages:
            return
        self.prev_stages.append(prev_stage)

        if prev_stage is None:
            return

        if isinstance(prev_stage, TaskSplitter):
            self.task_counter.append_counter(prev_stage.split_counter)
        elif isinstance(prev_stage, TaskRouter):
            self._pending_prev_bindings.append(prev_stage)
        else:
            self.task_counter.append_counter(prev_stage.success_counter)

    def set_stage_name(self, name: str = None):
        """
        设置当前节点名称

        :param name: 当前节点名称
        """
        self._name = name or f"Stage{id(self)}"

    def _finalize_prev_bindings(self):
        """
        绑定前置节点
        """
        from .task_nodes import TaskRouter

        if not self._pending_prev_bindings:
            return

        for prev_stage in self._pending_prev_bindings:
            if isinstance(prev_stage, TaskRouter):
                key = self.get_tag()  # 现在已经稳定了
                prev_stage.route_counters.setdefault(key, MPValue("i", 0))
                self.task_counter.append_counter(prev_stage.route_counters[key])

        self._pending_prev_bindings.clear()

    def get_stage_summary(self) -> dict:
        """
        获取当前节点的状态快照

        :return: 当前节点状态快照
        """
        return {
            "stage_mode": self.stage_mode,
            "execution_mode": self.get_execution_mode_desc(),
            "func_name": self.get_func_name(),
            "class_name": self.__class__.__name__,
        }

    def put_fail_queue(self, task, error, error_id):
        """
        将失败的任务放入失败队列

        :param task: 失败的任务
        :param error: 任务失败的异常
        """
        self.fail_queue.put(
            {
                "timestamp": time.time(),
                "stage_tag": self.get_tag(),
                "error_info": f"{type(error).__name__}({error})",
                "error_id": error_id,
                "task": str(task),
            }
        )

    def start_stage(
        self,
        input_queues: TaskQueue,
        output_queues: TaskQueue,
        fail_queue: MPQueue,
        logger_queue: MPQueue,
    ):
        """
        根据 start_type 的值，选择串行、并行执行任务

        :param input_queues: 输入队列
        :param output_queue: 输出队列
        :param fail_queue: 失败队列
        :param logger_queue: 日志队列
        """
        start_time = time.time()
        self.init_progress()
        self.init_env(input_queues, output_queues, fail_queue, logger_queue)
        self.task_logger.start_stage(
            self.get_tag(), self.execution_mode, self.worker_limit
        )

        try:
            # 根据模式运行对应的任务处理函数
            if self.execution_mode == "thread":
                self.run_with_executor(self.thread_pool)
            else:
                self.run_in_serial()

        finally:
            # cleanup_mpqueue(input_queues) # 会影响之后finalize_nodes
            self.result_queues.put(TERMINATION_SIGNAL)
            self.release_pool()

            self.progress_manager.close()
            self.task_logger.end_stage(
                self.get_tag(),
                self.execution_mode,
                time.time() - start_time,
                self.success_counter.value,
                self.error_counter.value,
                self.duplicate_counter.value,
            )
