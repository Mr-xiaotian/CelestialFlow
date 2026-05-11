# Benchmark

> 📅 最終更新日: 2026/05/11

`utils/benchmark.py` は、エグゼキュータおよびタスクグラフのパフォーマンスベンチマーク機能を提供し、異なる実行モード間のパフォーマンス差を比較するために使用されます。

## 設計目的

実際のプロジェクトでは、適切な実行モードの選択がパフォーマンスにとって非常に重要です。ベンチマークツールでは以下が可能です:
- 異なる実行モード間の実行時間を比較
- 並列化効果を検証
- パフォーマンスボトルネックを発見

## 主要関数

### benchmark_executor

`TaskExecutor` のベンチマークを実行します。

```python
async def benchmark_executor(
    sync_executor: TaskExecutor,
    async_executor: TaskExecutor,
    task_source: Iterable,
    sync_modes: list[str] | None = None,
    async_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    エグゼキュータのベンチマークを実行します。

    :param sync_executor: 同期エグゼキュータテンプレート
    :param async_executor: 非同期エグゼキュータテンプレート
    :param task_source: タスクソース
    :param sync_modes: 同期モードリスト、デフォルトは ["serial", "thread"]
    :param async_modes: 非同期モードリスト、デフォルトは ["async"]
    :return: テスト結果辞書
    """
```

出力例:
```
           Time
serial     2.34s
thread     0.89s
async      0.67s
```

### benchmark_graph

`TaskGraph` のベンチマークを実行します。

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
    タスクグラフのベンチマークを実行します。

    :param sync_graph: 同期タスクグラフテンプレート（serial/thread モード用）
    :param async_graph: 非同期タスクグラフテンプレート（async モード用）
    :param init_tasks_dict: 初期タスク辞書
    :param stage_modes: ステージモードリスト、デフォルトは ["serial", "thread"]
    :param execution_sync_modes: 同期実行モードリスト、デフォルトは ["serial", "thread"]
    :param execution_async_modes: 非同期実行モードリスト、デフォルトは ["async"]
    :return: テスト結果辞書
    """
```

出力例:
```
Time table:
          serial    thread    async
serial    5.23s     3.45s     3.21s
thread    2.12s     1.89s     1.65s
```

## 使用例

### エグゼキュータのテスト

```python
import asyncio
from celestialflow import TaskExecutor
from celestialflow.utils.benchmark import benchmark_executor

# 同期タスクの定義
def sync_task(x):
    return x * 2

# 非同期タスクの定義
async def async_task(x):
    await asyncio.sleep(0.01)
    return x * 2

# エグゼキュータの作成
sync_executor = TaskExecutor("SyncBench", sync_task)
async_executor = TaskExecutor("AsyncBench", async_task)

# ベンチマークの実行
asyncio.run(benchmark_executor(
    sync_executor=sync_executor,
    async_executor=async_executor,
    task_source=range(1000),
))
```

### タスクグラフのテスト

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.utils.benchmark import benchmark_graph

# 同期ステージの作成
stage_a = TaskStage("A", process_a)
stage_b = TaskStage("B", process_b)

# 非同期ステージの作成
async_stage_a = TaskStage("A", async_process_a)
async_stage_b = TaskStage("B", async_process_b)

# 同期グラフの構築
sync_graph = TaskGraph()
sync_graph.set_stages(root_stages=[stage_a], stages=[stage_a, stage_b])
sync_graph.connect([stage_a], [stage_b])

# 非同期グラフの構築
async_graph = TaskGraph()
async_graph.set_stages(root_stages=[async_stage_a], stages=[async_stage_a, async_stage_b])
async_graph.connect([async_stage_a], [async_stage_b])

# ベンチマークの実行
benchmark_graph(
    sync_graph=sync_graph,
    async_graph=async_graph,
    init_tasks_dict={stage_a.get_tag(): range(100)},
)
```

## テストマトリクス

### エグゼキュータテスト次元

| 次元 | 説明 |
|------|------|
| `serial` | シングルスレッド直列実行 |
| `thread` | スレッドプール並行実行 |
| `async` | コルーチン非同期実行 |

### タスクグラフテスト次元

**Stage Mode（ステージモード）**:
- `serial`: ステージがメインスレッドで実行
- `thread`: ステージが独立スレッドで実行

**Execution Mode（実行モード）**:
- `serial`: ステージ内部で直列実行
- `thread`: ステージ内部でスレッドプール実行
- `async`: ステージ内部でコルーチン非同期実行

組み合わせ例:
| Stage \ Execution | serial | thread | async |
|-------------------|--------|--------|-------|
| serial | S-S | S-T | S-A |
| thread | T-S | T-T | T-A |

## 出力情報

### 時間テーブル

各構成の実行時間を表示します。

### 失敗統計

タスクの失敗がある場合、以下が出力されます:
- `Fail stage dict`: ステージ別にグループ化された失敗タスク
- `Fail error dict`: エラー種別にグループ化された失敗タスク

## 注意事項

1. **クローンメカニズム**: 各テストは元のオブジェクトをクローンし、状態汚染を防ぎます
2. **タスク固定**: すべてのテストで同じタスクリストを使用し、公平性を保証します
3. **リソース競合**: スレッドモードではリソース競合により結果が影響される場合があります。複数回のテストを推奨します
4. **非同期要件**: `benchmark_executor` は非同期関数であり、`await` または `asyncio.run` が必要です
5. **グラフの分離**: `benchmark_graph` は async 実行モードに async 関数が必要なため、sync_graph と async_graph を別々に提供する必要があります
