import os
import time
from dotenv import load_dotenv

from celestialflow import (
    TaskStage,
    TaskChain,
    TaskSplitter,
)

def no_op(n):
    return n

load_dotenv()
ctree_host = os.getenv("CTREE_HOST")
ctree_http_port = os.getenv("CTREE_HTTP_PORT")
ctree_grpc_port = os.getenv("CTREE_GRPC_PORT")

def bench_no_ctree():
    # 定义任务节点
    task_splitter = TaskSplitter()
    process_stage = TaskStage(no_op, execution_mode="thread", worker_limit=50)

    chain = TaskChain([task_splitter, process_stage], "process", log_level="INFO")
    chain.set_ctree(
        False
    )

    start_time = time.time()
    chain.start_chain(
        {
            task_splitter.get_tag(): [range(int(1e4))],
        }
    )
    end_time = time.time()
    print(f"bench_no_ctree: {end_time - start_time}")

def bench_http_ctree():
    # 定义任务节点
    task_splitter = TaskSplitter()
    process_stage = TaskStage(no_op, execution_mode="thread", worker_limit=50)

    chain = TaskChain([task_splitter, process_stage], "process", log_level="INFO")
    chain.set_ctree(
        True, host=ctree_host, http_port=ctree_http_port, grpc_port=ctree_grpc_port, transport="http"
    )

    start_time = time.time()
    chain.start_chain(
        {
            task_splitter.get_tag(): [range(int(1e4))],
        }
    )
    end_time = time.time()
    print(f"bench_http_ctree: {end_time - start_time}")

def bench_grpc_ctree():
    # 定义任务节点
    task_splitter = TaskSplitter()
    process_stage = TaskStage(no_op, execution_mode="thread", worker_limit=50)

    chain = TaskChain([task_splitter, process_stage], "process", log_level="INFO")
    chain.set_ctree(
        True, host=ctree_host, http_port=ctree_http_port, grpc_port=ctree_grpc_port, transport="grpc"
    )

    start_time = time.time()
    chain.start_chain(
        {
            task_splitter.get_tag(): [range(int(1e4))],
        }
    )
    end_time = time.time()
    print(f"bench_grpc_ctree: {end_time - start_time}")

def main():
    bench_no_ctree()
    bench_http_ctree()
    bench_grpc_ctree()

if __name__ == "__main__":
    main()