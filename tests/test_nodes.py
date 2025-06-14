import pytest, logging, re, random, pprint
from time import sleep
from celestialvault.tools.TextTools import format_table
from celestialflow import TaskManager, TaskTree, TaskSplitter, TaskRedisTransfer, TaskLoop

def sleep_1(n):
    sleep(1)
    return n

def add_sleep(n):
    sleep(1)
    if n > 10:
        raise ValueError("Test error for greater than 10")
    elif n == 0:
        raise ValueError("Test error for 0")
    return n + 1

def fibonacci(n):
    if n <= 0:
        raise ValueError("n must be a positive integer")
    elif n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)
    
def generate_urls(x):
    return tuple([f"url_{x}_{i}" for i in range(random.randint(1, 4))])

def log_urls(data):
    if data == ('url_1_0', 'url_1_1'):
        raise ValueError("Test error in ('url_1_0', 'url_1_1')")
    return f"Logged({data})"

def download(url):
    if "url_3" in url:
        raise ValueError("Test error in url_3_*")
    return f"Downloaded({url})"

def parse(url):
    num_list = re.findall(r'\d+', url)
    parse_num = int("".join(num_list))
    if parse_num > 100:
        raise ValueError("Test error for greater than 100")
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

def _test_splitter_0():    
    # 定义任务节点
    generate_stage = TaskManager(func=generate_urls, execution_mode='thread', worker_limit=4)
    logger_stage = TaskManager(func=log_urls, execution_mode='thread', worker_limit=4)
    splitter = TaskSplitter()
    download_stage = TaskManager(func=download, execution_mode='thread', worker_limit=4)
    parse_stage = TaskManager(func=parse, execution_mode='thread', worker_limit=4)

    # 设置链关系
    generate_stage.set_tree_context([logger_stage, splitter], stage_mode='process', stage_name='GenURLs')
    logger_stage.set_tree_context([], stage_mode='process', stage_name='Loger')
    splitter.set_tree_context([download_stage, parse_stage], stage_mode='process', stage_name='Splitter')
    download_stage.set_tree_context([], stage_mode='process', stage_name='Downloader')
    parse_stage.set_tree_context([], stage_mode='process', stage_name='Parser')

    # 初始化 TaskTree
    tree = TaskTree(generate_stage)

    # 测试输入：生成不同 URL 的任务
    input_tasks = {
        generate_stage.get_stage_tag(): range(10),
    }
    stage_modes = ['serial', 'process']
    execution_modes = ['serial', 'thread']

    result = tree.test_methods(input_tasks, stage_modes, execution_modes)
    test_table_list, execution_modes, stage_modes, index_header = result["Time table"]
    result["Time table"] = format_table(test_table_list, column_names = execution_modes, row_names = stage_modes, index_header = index_header)

    for key, value in result.items():
        if isinstance(value, dict):
            value = pprint.pformat(value)
        logging.info(f"{key}: \n{value}")

def _test_splitter_1():
    # 定义任务节点
    generate_stage = TaskManager(func=generate_urls_sleep, execution_mode='thread', worker_limit=4)
    logger_stage = TaskManager(func=log_urls_sleep, execution_mode='thread', worker_limit=4)
    splitter = TaskSplitter()
    download_stage = TaskManager(func=download_sleep, execution_mode='thread', worker_limit=4)
    parse_stage = TaskManager(func=parse_sleep, execution_mode='thread', worker_limit=4)

    # 设置链关系
    generate_stage.set_tree_context([logger_stage, splitter], stage_mode='process', stage_name='GenURLs')
    logger_stage.set_tree_context([], stage_mode='process', stage_name='Loger')
    splitter.set_tree_context([download_stage, parse_stage], stage_mode='process', stage_name='Splitter')
    download_stage.set_tree_context([], stage_mode='process', stage_name='Downloader')
    parse_stage.set_tree_context([generate_stage], stage_mode='process', stage_name='Parser')

    # 初始化 TaskTree
    tree = TaskTree(generate_stage)
    tree.set_reporter(True, host="127.0.0.1", port=5005)

    tree.start_tree({
        generate_stage.get_stage_tag(): range(10),
        # logger_stage.get_stage_tag(): tuple([f"url_{x}_{i}" for i in range(random.randint(1, 4)) for x in range(10, 15)]),
        # splitter.get_stage_tag(): tuple([f"url_{x}_{i}" for i in range(random.randint(1, 4)) for x in range(10, 15)]),
        download_stage.get_stage_tag(): [f"url_{x}_5" for x in range(10, 20)],
        # parse_stage.get_stage_tag(): [f"url_{x}_5" for x in range(10, 20)],
    }, False)

def _test_transfer():
    root_stage = TaskManager(sleep_1, 'thread', 3)
    redis_transfer = TaskRedisTransfer()
    fibonacci_stage = TaskManager(fibonacci, 'thread')

    root_stage.set_tree_context([redis_transfer, fibonacci_stage], stage_mode='serial', stage_name='Root')
    redis_transfer.set_tree_context([], stage_mode='process', stage_name='GoFibonacci')
    fibonacci_stage.set_tree_context([], stage_mode='process', stage_name='Fibonacci')

    tree = TaskTree(root_stage)
    tree.set_reporter(True, host="127.0.0.1", port=5005)

    # 要测试的任务列表
    test_task_0 = range(25, 37)
    test_task_1 = list(test_task_0) + [0, 27, None, 0, '']

    tree.start_tree({
        root_stage.get_stage_tag(): test_task_0,
    })

def test_loop():
    stageA = TaskManager(add_sleep, 'thread', 3)
    stageB = TaskManager(add_sleep, 'thread', 3)
    stageC = TaskManager(add_sleep, 'thread', 3)

    tree = TaskLoop([stageA, stageB, stageC], chain_mode="process")
    tree.set_reporter(True, host="127.0.0.1", port=5005)

    # 要测试的任务列表
    test_task_0 = range(1, 2)
    test_task_1 = list(test_task_0) + [0, 6, None, 0, '']

    tree.start_loop({
        stageA.get_stage_tag(): test_task_0
    })

if __name__ == '__main__':
    # test_splitter_1()
    pass