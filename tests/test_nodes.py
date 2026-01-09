import pytest, logging, re, random, os
import requests
from time import sleep
from dotenv import load_dotenv

from celestialflow import (
    TaskStage,
    TaskGraph,
    TaskChain,
    TaskSplitter,
    TaskRedisSink,
    TaskRedisSource,
    TaskRedisAck,
    TaskRouter,
)


load_dotenv()
report_host = os.getenv("REPORT_HOST")
report_port = os.getenv("REPORT_PORT")

redis_host = os.getenv("REDIS_HOST")
redis_password = os.getenv("REDIS_PASSWORD")

ctree_host = os.getenv("CTREE_HOST")
ctree_port = os.getenv("CTREE_PORT")


class DownloadRedisSink(TaskRedisSink):
    def get_args(self, task):
        url, path = task
        return url, path.replace("/tmp/", "X:/Download/download_go/")


class DownloadStage(TaskStage):
    def get_args(self, task):
        url, path = task
        return url, path.replace("/tmp/", "X:/Download/download_py/")


def no_op(n):
    return n


def sleep_1(n):
    sleep(1)
    return n


def fibonacci(n):
    if n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)


def generate_urls(x):
    return tuple([f"url_{x}_{i}" for i in range(random.randint(1, 4))])


def log_urls(data):
    if data == ("url_1_0", "url_1_1"):
        raise ValueError("Test error in ('url_1_0', 'url_1_1')")
    return f"Logged({data})"


def download(url):
    if "url_3" in url:
        raise ValueError("Test error in url_3_*")
    return f"Downloaded({url})"


def parse(url):
    num_list = re.findall(r"\d+", url)
    parse_num = int("".join(num_list))
    if parse_num % 2 == 0:
        raise ValueError("Test error for even")
    elif parse_num % 3 == 0:
        raise ValueError("Test error for multiple of 3")
    elif parse_num == 0:
        raise ValueError("Test error for 0")
    return parse_num


def generate_urls_sleep(x):
    sleep(random.randint(4, 6))
    return generate_urls(x)


def log_urls_sleep(url):
    sleep(random.randint(4, 6))
    return log_urls(url)


def download_sleep(url):
    sleep(random.randint(4, 6))
    return download(url)


def parse_sleep(url):
    sleep(random.randint(4, 6))
    return parse(url)


def sum_int(*num):
    return sum(num)


def add_one(num):
    return num + 1


def sqrt(num):
    return num**0.5


def download_to_file(url: str, file_path: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 如果状态码不是 200 会抛出异常

        with open(file_path, "wb") as f:
            f.write(response.content)

        return f"Downloaded {url} → {file_path}"
    except Exception as e:
        raise RuntimeError(f"Download failed: {e}")


def test_splitter_0():
    # 定义任务节点
    generate_stage = TaskStage(
        func=generate_urls_sleep, execution_mode="thread", worker_limit=4
    )
    logger_stage = TaskStage(
        func=log_urls_sleep, execution_mode="thread", worker_limit=4
    )
    splitter = TaskSplitter()
    download_stage = TaskStage(
        func=download_sleep, execution_mode="thread", worker_limit=4
    )
    parse_stage = TaskStage(func=parse_sleep, execution_mode="thread", worker_limit=4)

    # 设置链关系
    generate_stage.set_graph_context(
        [logger_stage, splitter], stage_mode="process", stage_name="GenURLs"
    )
    logger_stage.set_graph_context([], stage_mode="process", stage_name="Loger")
    splitter.set_graph_context(
        [download_stage, parse_stage], stage_mode="process", stage_name="Splitter"
    )
    download_stage.set_graph_context([], stage_mode="process", stage_name="Downloader")
    parse_stage.set_graph_context(
        [generate_stage], stage_mode="process", stage_name="Parser"
    )

    # 初始化 TaskGraph
    graph = TaskGraph([generate_stage])
    graph.set_reporter(True, host=report_host, port=report_port)

    graph.start_graph(
        {
            generate_stage.get_tag(): range(10),
            # logger_stage.get_tag(): tuple([f"url_{x}_{i}" for i in range(random.randint(1, 4)) for x in range(10, 15)]),
            # splitter.get_tag(): tuple([f"url_{x}_{i}" for i in range(random.randint(1, 4)) for x in range(10, 15)]),
            # download_stage.get_tag(): [f"url_{x}_5" for x in range(10, 20)],
            # parse_stage.get_tag(): [f"url_{x}_5" for x in range(10, 20)],
        },
        False,
    )


def test_splitter_1():
    # 定义任务节点
    task_splitter = TaskSplitter()
    process_stage = TaskStage(no_op, execution_mode="thread", worker_limit=50)

    chain = TaskChain([task_splitter, process_stage], "process")
    chain.set_reporter(True, host=report_host, port=report_port)

    chain.start_chain(
        {
            task_splitter.get_tag(): [range(int(1e5))],
        }
    )


def test_redis_ack_0():
    start_stage = TaskStage(sleep_1, execution_mode="thread", worker_limit=4)
    redis_sink = TaskRedisSink(
        key="testFibonacci:input", host=redis_host, password=redis_password
    )
    redis_ack = TaskRedisAck(
        key="testFibonacci:output", host=redis_host, password=redis_password
    )
    fibonacci_stage = TaskStage(fibonacci, "thread")

    start_stage.set_graph_context(
        [redis_sink, fibonacci_stage], stage_mode="serial", stage_name="Start"
    )
    redis_sink.set_graph_context(
        [redis_ack], stage_mode="process", stage_name="RedisSink"
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
    start_stage = TaskStage(sleep_1, execution_mode="thread", worker_limit=4)
    redis_sink = TaskRedisSink(
        key="testSum:input",
        host=redis_host,
        password=redis_password,
        unpack_task_args=True,
    )
    redis_ack = TaskRedisAck(
        key="testSum:output", host=redis_host, password=redis_password
    )
    sum_stage = TaskStage(
        sum_int, execution_mode="thread", worker_limit=4, unpack_task_args=True
    )

    start_stage.set_graph_context(
        [redis_sink, sum_stage], stage_mode="serial", stage_name="Start"
    )
    redis_sink.set_graph_context(
        [redis_ack], stage_mode="process", stage_name="RedisSink"
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
    start_stage = TaskStage(sleep_1, execution_mode="thread", worker_limit=4)
    redis_sink = DownloadRedisSink(
        key="testDownload:input",
        host=redis_host,
        password=redis_password,
        unpack_task_args=True,
    )
    redis_ack = TaskRedisAck(
        key="testDownload:output", host=redis_host, password=redis_password
    )
    download_stage = DownloadStage(
        download_to_file, execution_mode="thread", worker_limit=4
    )

    start_stage.set_graph_context(
        [redis_sink, download_stage], stage_mode="serial", stage_name="Start"
    )
    redis_sink.set_graph_context(
        [redis_ack], stage_mode="process", stage_name="RedisSink"
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
    redis_sink = TaskRedisSink("test_redis", host=redis_host, password=redis_password)
    redis_source = TaskRedisSource(
        "test_redis", host=redis_host, password=redis_password
    )
    sleep_stage_1 = TaskStage(sleep_1, execution_mode="serial")

    sleep_stage_0.set_graph_context(
        [redis_sink], stage_mode="process", stage_name="Sleep0"
    )
    redis_sink.set_graph_context([], stage_mode="process", stage_name="RedisSink")
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
    stage_a = TaskStage(func=sleep_1, execution_mode="thread", worker_limit=2)
    stage_b = TaskStage(func=sleep_1, execution_mode="thread", worker_limit=2)

    router.set_graph_context(
        [stage_a, stage_b], stage_mode="serial", stage_name="Router"
    )
    stage_a.set_graph_context([], stage_mode="process", stage_name="Stage A")
    stage_b.set_graph_context([], stage_mode="process", stage_name="Stage B")

    a_tag = stage_a.get_tag()
    b_tag = stage_b.get_tag()

    def to_route_task(n: int) -> tuple:
        target = a_tag if (n % 2 == 0) else b_tag
        return (target, n)

    graph = TaskGraph([router])
    graph.set_reporter(True, host=report_host, port=report_port)

    graph.start_graph(
        {
            router.get_tag(): [to_route_task(i) for i in range(20)],
        }
    )


if __name__ == "__main__":
    # test_splitter_1()
    test_router_0()
    pass
