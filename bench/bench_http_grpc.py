import os
import time
from typing import Any

from dotenv import load_dotenv

from celestialflow import (
    TaskChain,
    TaskSplitter,
    TaskStage,
)


def no_op(n: Any) -> Any:
    return n


load_dotenv()
ctree_host = os.getenv("CTREE_HOST", "127.0.0.1")
ctree_http_port = int(os.getenv("CTREE_HTTP_PORT", "7777"))
ctree_grpc_port = int(os.getenv("CTREE_GRPC_PORT", "7778"))


def bench_no_ctree() -> None:
    # 定义任务节点
    task_splitter = TaskSplitter("splitter")
    process_stage = TaskStage(
        "ProcessNoOp", no_op, execution_mode="thread", max_workers=50
    )

    chain = TaskChain([task_splitter, process_stage], "thread", log_level="INFO")
    chain.set_ctree(False)

    start_time = time.perf_counter()
    chain.start_chain(
        {
            task_splitter.get_name(): [range(int(1e4))],
        }
    )
    end_time = time.perf_counter()
    print(f"bench_no_ctree: {end_time - start_time}")


def bench_http_ctree() -> None:
    # 定义任务节点
    task_splitter = TaskSplitter("splitter")
    process_stage = TaskStage(
        "ProcessNoOp", no_op, execution_mode="thread", max_workers=50
    )

    chain = TaskChain([task_splitter, process_stage], "thread", log_level="INFO")
    chain.set_ctree(
        True,
        host=ctree_host,
        http_port=ctree_http_port,
        grpc_port=ctree_grpc_port,
        transport="http",
    )

    start_time = time.perf_counter()
    chain.start_chain(
        {
            task_splitter.get_name(): [range(int(1e4))],
        }
    )
    end_time = time.perf_counter()
    print(f"bench_http_ctree: {end_time - start_time}")


def bench_grpc_ctree() -> None:
    # 定义任务节点
    task_splitter = TaskSplitter("splitter")
    process_stage = TaskStage(
        "ProcessNoOp", no_op, execution_mode="thread", max_workers=50
    )

    chain = TaskChain([task_splitter, process_stage], "thread", log_level="INFO")
    chain.set_ctree(
        True,
        host=ctree_host,
        http_port=ctree_http_port,
        grpc_port=ctree_grpc_port,
        transport="grpc",
    )

    start_time = time.perf_counter()
    chain.start_chain(
        {
            task_splitter.get_name(): [range(int(1e4))],
        }
    )
    end_time = time.perf_counter()
    print(f"bench_grpc_ctree: {end_time - start_time}")


def main() -> None:
    bench_no_ctree()
    bench_http_ctree()
    bench_grpc_ctree()


if __name__ == "__main__":
    main()
