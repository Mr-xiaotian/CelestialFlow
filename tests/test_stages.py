import logging
import os
import random

import dill
import pytest
from test_utils import (
    RouterWrapper,
    download_sleep,
    download_to_file,
    fibonacci,
    generate_urls_sleep,
    log_urls_sleep,
    no_op,
    parse_sleep,
    sleep_1,
    sum_int,
)

from celestialflow import (
    TaskChain,
    TaskGraph,
    TaskRedisAck,
    TaskRedisSource,
    TaskRedisTransport,
    TaskRouter,
    TaskSplitter,
    TaskStage,
)

report_host = os.getenv("REPORT_HOST")
report_port = os.getenv("REPORT_PORT")

redis_host = os.getenv("REDIS_HOST")
redis_password = os.getenv("REDIS_PASSWORD")

ctree_host = os.getenv("CTREE_HOST")
ctree_http_port = os.getenv("CTREE_HTTP_PORT")
ctree_grpc_port = os.getenv("CTREE_GRPC_PORT")


class DownloadRedisTransport(TaskRedisTransport):
    def get_args(self, task):
        url, path = task
        return url, path.replace("/tmp/", "X:/Download/download_go/")


class DownloadStage(TaskStage):
    def get_args(self, task):
        url, path = task
        return url, path.replace("/tmp/", "X:/Download/download_py/")


def test_splitter_0():
    # 定义任务节点
    generate_stage = TaskStage(
        func=generate_urls_sleep, execution_mode="thread", max_workers=4
    )
    logger_stage = TaskStage(
        func=log_urls_sleep, execution_mode="thread", max_workers=4
    )
    splitter = TaskSplitter()
    download_stage = TaskStage(
        func=download_sleep, execution_mode="thread", max_workers=4
    )
    parse_stage = TaskStage(func=parse_sleep, execution_mode="thread", max_workers=4)

    # 设置链关系
    generate_stage.set_graph_context(
        [logger_stage, splitter], stage_mode="process", stage_name="GenURLs"
    )
    logger_stage.set_graph_context([], stage_mode="process", stage_name="Logger")
    splitter.set_graph_context(
        [download_stage, parse_stage], stage_mode="process", stage_name="Splitter"
    )
    download_stage.set_graph_context([], stage_mode="process", stage_name="Downloader")
    parse_stage.set_graph_context(
        [generate_stage], stage_mode="process", stage_name="Parser"
    )

    # 初始化 TaskGraph
    graph = TaskGraph([generate_stage], log_level="INFO")
    graph.set_reporter(True, host=report_host, port=report_port)
    graph.set_ctree(
        True, host=ctree_host, http_port=ctree_http_port, grpc_port=ctree_grpc_port
    )

    graph.start_graph(
        {
            generate_stage.get_tag(): range(10),
            # logger_stage.get_tag(): tuple([f"url_{x}_{i}" for i in range(random.randint(1, 4)) for x in range(10, 15)]),
            # splitter.get_tag(): tuple([f"url_{x}_{i}" for i in range(random.randint(1, 4)) for x in range(10, 15)]),
            # download_stage.get_tag(): [f"url_{x}_5" for x in range(10, 20)],
            # parse_stage.get_tag(): [f"url_{x}_5" for x in range(10, 20)],
        },
        True,
    )

    # print()
    # print(graph.get_stage_input_trace(generate_stage.get_tag()))


def test_splitter_1():
    # 定义任务节点
    task_splitter = TaskSplitter()
    process_stage = TaskStage(no_op, execution_mode="thread", max_workers=50)

    chain = TaskChain([task_splitter, process_stage], "process", log_level="INFO")
    chain.set_reporter(True, host=report_host, port=report_port)
    chain.set_ctree(
        True,
        host=ctree_host,
        http_port=ctree_http_port,
        grpc_port=ctree_grpc_port,
        transport="grpc",
    )

    chain.start_chain(
        {
            task_splitter.get_tag(): [range(int(1e5))],
        }
    )


def test_redis_ack_0():
    start_stage = TaskStage(sleep_1, execution_mode="thread", max_workers=4)
    redis_tranport = TaskRedisTransport(
        key="testFibonacci:input", host=redis_host, password=redis_password
    )
    redis_ack = TaskRedisAck(
        key="testFibonacci:output", host=redis_host, password=redis_password
    )
    fibonacci_stage = TaskStage(fibonacci, "thread")

    start_stage.set_graph_context(
        [redis_tranport, fibonacci_stage], stage_mode="serial", stage_name="Start"
    )
    redis_tranport.set_graph_context(
        [redis_ack], stage_mode="process", stage_name="RedisTransport"
    )
    redis_ack.set_graph_context([], stage_mode="process", stage_name="RedisAck")
    fibonacci_stage.set_graph_context([], stage_mode="process", stage_name="Fibonacci")

    graph = TaskGraph([start_stage])
    graph.set_reporter(True, host=report_host, port=report_port)

    # 要测试的任务列表
    test_task_0 = range(25, 37)
    test_task_1 = list(test_task_0) + [0, 27, None, 0, ""]

    graph.start_graph(
        {
            start_stage.get_tag(): test_task_1,
        }
    )


def test_redis_ack_1():
    start_stage = TaskStage(sleep_1, execution_mode="thread", max_workers=4)
    redis_tranport = TaskRedisTransport(
        key="testSum:input",
        host=redis_host,
        password=redis_password,
        unpack_task_args=True,
    )
    redis_ack = TaskRedisAck(
        key="testSum:output", host=redis_host, password=redis_password
    )
    sum_stage = TaskStage(
        sum_int, execution_mode="thread", max_workers=4, unpack_task_args=True
    )

    start_stage.set_graph_context(
        [redis_tranport, sum_stage], stage_mode="serial", stage_name="Start"
    )
    redis_tranport.set_graph_context(
        [redis_ack], stage_mode="process", stage_name="RedisTransport"
    )
    redis_ack.set_graph_context([], stage_mode="process", stage_name="RedisAck")
    sum_stage.set_graph_context([], stage_mode="process", stage_name="Sum")

    graph = TaskGraph([start_stage])
    graph.set_reporter(True, host=report_host, port=report_port)

    # 要测试的任务列表
    test_task_0 = [(random.randint(1, 100), random.randint(1, 100)) for _ in range(12)]

    graph.start_graph(
        {
            start_stage.get_tag(): test_task_0,
        }
    )


def test_redis_ack_2():
    start_stage = TaskStage(sleep_1, execution_mode="thread", max_workers=4)
    redis_tranport = DownloadRedisTransport(
        key="testDownload:input",
        host=redis_host,
        password=redis_password,
        unpack_task_args=True,
    )
    redis_ack = TaskRedisAck(
        key="testDownload:output", host=redis_host, password=redis_password
    )
    download_stage = DownloadStage(
        download_to_file, execution_mode="thread", max_workers=4
    )

    start_stage.set_graph_context(
        [redis_tranport, download_stage], stage_mode="serial", stage_name="Start"
    )
    redis_tranport.set_graph_context(
        [redis_ack], stage_mode="process", stage_name="RedisTransport"
    )
    redis_ack.set_graph_context([], stage_mode="process", stage_name="RedisAck")
    download_stage.set_graph_context([], stage_mode="process", stage_name="Download")

    graph = TaskGraph([start_stage])
    graph.set_reporter(True, host=report_host, port=report_port)

    download_links = [
        # # 小型 HTML 页面
        # ["https://example.com", "/tmp/example.html"],
        # ["https://www.iana.org/domains/example", "/tmp/iana.html"],
        # # 文本文件（GitHub RAW）
        # ["https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore", "/tmp/python.gitignore"],
        # 小图片
        [
            "https://img.4khd.com/-IaKPu2ONWz8/aEhVCP-4Wsl/AAAAAAADirM/2Fg5CujCaKk7PqPY3I6DELSmidZE3ofqgCNcBGAsHYQ/w1300-rw/orts-shoes-4khd.com-001.webp?w=1300",
            "/tmp/orts-shoes-4khd.com-001.png",
        ],
        [
            "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/2949210/ss_a2792205c92812f5be3321f2e685135b402e5a72.600x338.jpg?t=1714466877",
            "/tmp/steam_2949210.jpg",
        ],
        # JSON 示例（可保存为 .json 文件）
        # ["https://jsonplaceholder.typicode.com/todos/1", "/tmp/todo1.json"],
    ]

    graph.start_graph({start_stage.get_tag(): download_links})


def test_redis_source_0():
    sleep_stage_0 = TaskStage(sleep_1, execution_mode="serial")
    redis_tranport = TaskRedisTransport(
        "test_redis", host=redis_host, password=redis_password
    )
    redis_source = TaskRedisSource(
        "test_redis", host=redis_host, password=redis_password
    )
    sleep_stage_1 = TaskStage(sleep_1, execution_mode="serial")

    sleep_stage_0.set_graph_context(
        [redis_tranport], stage_mode="process", stage_name="Sleep0"
    )
    redis_tranport.set_graph_context(
        [], stage_mode="process", stage_name="RedisTransport"
    )
    redis_source.set_graph_context(
        [sleep_stage_1], stage_mode="process", stage_name="RedisSource"
    )
    sleep_stage_1.set_graph_context([], stage_mode="process", stage_name="Sleep1")

    graph = TaskGraph([sleep_stage_0, redis_source])
    graph.set_reporter(True, host=report_host, port=report_port)

    # 要测试的任务列表
    test_task_0 = range(25, 37)

    graph.start_graph(
        {
            sleep_stage_0.get_tag(): test_task_0,
            redis_source.get_tag(): range(12),
        }
    )


def test_router_0():
    router = TaskRouter()
    stage_a = TaskStage(func=sleep_1, execution_mode="thread", max_workers=2)
    stage_b = TaskStage(func=sleep_1, execution_mode="thread", max_workers=2)

    router.set_graph_context(
        [stage_a, stage_b], stage_mode="serial", stage_name="Router"
    )
    stage_a.set_graph_context([], stage_mode="process", stage_name="Stage A")
    stage_b.set_graph_context([], stage_mode="process", stage_name="Stage B")

    a_tag = stage_a.get_tag()
    b_tag = stage_b.get_tag()

    source_stage = TaskStage(
        RouterWrapper(a_tag, b_tag), execution_mode="thread", max_workers=4
    )

    source_stage.set_graph_context([router], stage_mode="serial", stage_name="Origin")

    graph = TaskGraph([source_stage])
    graph.set_reporter(True, host=report_host, port=report_port)

    graph.start_graph(
        {
            source_stage.get_tag(): range(20),
        }
    )


if __name__ == "__main__":
    # test_splitter_0()
    test_router_0()
    pass
