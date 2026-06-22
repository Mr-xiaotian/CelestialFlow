# Benchmark

> 📅 最終更新日: 2026/06/22

`utils/util_benchmark.py` は実行器とタスクグラフのパフォーマンスベンチマークテスト機能を提供し、異なる実行モードのパフォーマンス差異を比較します。

## 設計目的

実際のプロジェクトでは、適切な実行モードの選択がパフォーマンスに重要です。ベンチマークテストツールは以下を実現します：
- 異なる実行モードの実行時間を比較
- 並列化効果を検証
- パフォーマンスボトルネックを発見

## 主要関数

### benchmark_executor

`TaskExecutor` のベンチマークテストを行います。

```python
async def benchmark_executor(
    sync_executor: TaskExecutor,
    async_executor: TaskExecutor,
    task_source: Iterable,
    sync_modes: list[str] | None = None,
    async_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对执行器进行基准测试。

    :param sync_executor: 同步执行器模板
    :param async_executor: 异步执行器模板
    :param task_source: 任务源
    :param sync_modes: 同步模式列表，默认 ["serial", "thread"]
    :param async_modes: 异步模式列表，默认 ["async"]
    :return: 测试结果字典（含 use_time, sync_modes, async_modes, table）
    """
```

テストフロー：
1. 実行器をクローン（状態汚染を防止）
2. 各モードに実行方式を設定
3. タスクを実行して計測
4. 時間テーブルと結果テーブルを出力

出力例：
```
           Time
serial     2.34s
thread     0.89s
async      0.67s
```

### benchmark_graph

`TaskGraph` のベンチマークテストを行います。

```python
def benchmark_graph(
    sync_graph: TaskGraph,
    async_graph: TaskGraph,
    init_tasks_dict: Mapping[str, Iterable],
    stage_modes: list[str] | None = None,
    execution_sync_modes: list[str] | None = None,
    execution_async_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对任务图进行基准测试。

    :param sync_graph: 同步任务图模板（用于 serial/thread 模式）
    :param async_graph: 异步任务图模板（用于 async 模式）
    :param init_tasks_dict: 初始任务字典
    :param stage_modes: 节点模式列表，默认 ["serial", "thread"]
    :param execution_sync_modes: 同步执行模式列表，默认 ["serial", "thread"]
    :param execution_async_modes: 异步执行模式列表，默认 ["async"]
    :return: 测试结果字典（含 table, stage_modes, sync_modes, async_modes）
    """
```

テストフロー：
1. 各 `stage_mode` × `execution_mode` 組み合わせについて
2. タスクグラフをクローン
3. `set_graph_mode(stage_mode, execution_mode)` を設定
4. `start_graph()` を実行して計測
5. 時間テーブルを出力

出力例：
```
Time table:
          serial    thread    async
serial    5.23s     3.45s     3.21s
thread    2.12s     1.89s     1.65s
```

## 使用例

### 実行器のテスト

```python
import asyncio
from celestialflow import TaskExecutor
from celestialflow.utils.util_benchmark import benchmark_executor

# 定义同步任务
def sync_task(x):
    return x * 2

# 定义异步任务
async def async_task(x):
    await asyncio.sleep(0.01)
    return x * 2

# 创建执行器
sync_executor = TaskExecutor("SyncBench", sync_task)
async_executor = TaskExecutor("AsyncBench", async_task)

# 运行基准测试
asyncio.run(benchmark_executor(
    sync_executor=sync_executor,
    async_executor=async_executor,
    task_source=range(1000),
))
```

### タスクグラフのテスト

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.utils.util_benchmark import benchmark_graph


# 定义同步处理函数
def process_a(x: int) -> int:
    return x * 2


def process_b(x: int) -> int:
    return x + 1


# 定义异步处理函数
async def async_process_a(x: int) -> int:
    return x * 2


async def async_process_b(x: int) -> int:
    return x + 1


# 创建同步节点
stage_a = TaskStage("A", process_a)
stage_b = TaskStage("B", process_b)

# 创建异步节点
async_stage_a = TaskStage("A", async_process_a)
async_stage_b = TaskStage("B", async_process_b)

# 构建同步图
sync_graph = TaskGraph(name="SyncGraph")
sync_graph.set_stages(stages=[stage_a, stage_b])
sync_graph.connect([stage_a], [stage_b])

# 构建异步图
async_graph = TaskGraph(name="AsyncGraph")
async_graph.set_stages(stages=[async_stage_a, async_stage_b])
async_graph.connect([async_stage_a], [async_stage_b])

# 运行基准测试
benchmark_graph(
    sync_graph=sync_graph,
    async_graph=async_graph,
    init_tasks_dict={stage_a.get_name(): range(100)},
)
```

## テストマトリックス

### 実行器テストの次元

| 次元 | 説明 |
|------|------|
| `serial` | シングルスレッド逐次実行 |
| `thread` | スレッドプール並行実行 |
| `async` | コルーチン非同期実行 |

### タスクグラフテストの次元

**Stage Mode（ノードモード）**：
- `serial`: ノードをメインスレッドで実行
- `thread`: ノードを独立スレッドで実行

**Execution Mode（実行モード）**：
- `serial`: ノード内部で逐次実行
- `thread`: ノード内部でスレッドプール実行
- `async`: ノード内部でコルーチン非同期実行

組み合わせ例：
| Stage \ Execution | serial | thread | async |
|-------------------|--------|--------|-------|
| serial | S-S | S-T | S-A |
| thread | T-S | T-T | T-A |

## 出力情報

### 時間テーブル

各設定の実行時間を表示します。

### 結果テーブル

各設定の成功結果ペアを表示します。

### 戻り値

`benchmark_executor` は以下の内容を含む辞書を返します：
- `use_time`: 各モードの実行時間リスト
- `sync_modes`: テストされた同期モードリスト
- `async_modes`: テストされた非同期モードリスト
- `table`: フォーマット済みの時間テーブル文字列

`benchmark_graph` は以下の内容を含む辞書を返します：
- `table`: フォーマット済みの時間テーブル文字列
- `stage_modes`: テストされたノードモードリスト
- `sync_modes` / `async_modes`: テストされた実行モードリスト

## 注意事項

1. **クローン機構**: 各テストで元のオブジェクトをクローンし、状態汚染を防止
2. **タスク固定**: 全テストで同じタスクリストを使用し、公平性を確保
3. **リソース競合**: スレッドモードはリソース競合により結果が変動する可能性があります。複数回のテストを推奨
4. **非同期要件**: `benchmark_executor` は非同期関数であり、`await` または `asyncio.run` が必要
5. **グラフの分離**: `benchmark_graph` は sync_graph と async_graph を別々に提供する必要があります。async 実行モードには async 関数が必要なため
