import os

from dotenv import load_dotenv

from demo_utils import (
    async_double,
    async_to_str,
    extract_record,
    load_record,
    transform_enrich,
    transform_normalize,
)

from celestialflow import (
    TaskGraph,
    TaskStage,
)

load_dotenv()

report_host = os.getenv("REPORT_HOST")
report_port = os.getenv("REPORT_PORT")

redis_host = os.getenv("REDIS_HOST")
redis_password = os.getenv("REDIS_PASSWORD")

ctree_host = os.getenv("CTREE_HOST")
ctree_http_port = os.getenv("CTREE_HTTP_PORT")
ctree_grpc_port = os.getenv("CTREE_GRPC_PORT")


def demo_etl_fan_out_fan_in():
    """
    ETL pipeline with fan-out/fan-in topology:

        Extract ──┬── Normalize ──┬── Load
                  └── Enrich ─────┘

    Demonstrates:
    - Fan-out: one stage feeds two parallel downstream stages
    - Fan-in: two stages merge into one downstream stage
    - Mixed execution modes across stages
    - Querying graph summary after execution
    """
    extract = TaskStage(
        "Extract",
        extract_record,
        execution_mode="thread",
        max_workers=4,
        stage_mode="thread",
    )
    normalize = TaskStage(
        "Normalize",
        transform_normalize,
        execution_mode="thread",
        max_workers=4,
        stage_mode="thread",
    )
    enrich = TaskStage(
        "Enrich",
        transform_enrich,
        execution_mode="thread",
        max_workers=4,
        stage_mode="thread",
    )
    load = TaskStage(
        "Load",
        load_record,
        execution_mode="serial",
        stage_mode="thread",
    )

    graph = TaskGraph(schedule_mode="eager", log_level="INFO")
    graph.set_reporter(True, host=report_host, port=report_port)
    graph.set_stages(
        root_stages=[extract],
        stages=[normalize, enrich, load],
    )
    graph.connect([extract], [normalize, enrich])
    graph.connect([normalize, enrich], [load])

    raw_ids = list(range(1, 16))
    graph.start_graph({extract.get_tag(): raw_ids})

    summary = graph.get_graph_summary()
    print(f"Total succeeded: {summary.get('total_succeeded', 0)}")
    print(f"Total failed:    {summary.get('total_failed', 0)}")


def demo_async_staged_pipeline():
    """
    Two-stage async pipeline with staged scheduling:

        AsyncDouble ──> AsyncToStr

    Demonstrates:
    - execution_mode="async" for coroutine-based task functions
    - schedule_mode="staged" for layer-by-layer execution
    - Retrieving per-stage status after completion
    """
    stage_double = TaskStage(
        "AsyncDouble",
        async_double,
        execution_mode="async",
        max_workers=8,
        stage_mode="thread",
    )
    stage_to_str = TaskStage(
        "AsyncToStr",
        async_to_str,
        execution_mode="async",
        max_workers=8,
        stage_mode="thread",
    )

    graph = TaskGraph(schedule_mode="staged", log_level="INFO")
    graph.set_reporter(True, host=report_host, port=report_port)
    graph.set_stages(
        root_stages=[stage_double],
        stages=[stage_to_str],
    )
    graph.connect([stage_double], [stage_to_str])

    tasks = list(range(1, 21))
    graph.start_graph({stage_double.get_tag(): tasks})

    status = graph.get_status_dict()
    for tag, info in status.items():
        print(f"[{tag}] succeeded={info.get('tasks_succeeded', 0)}, "
              f"failed={info.get('tasks_failed', 0)}")


if __name__ == "__main__":
    demo_etl_fan_out_fan_in()
    demo_async_staged_pipeline()

