# Benchmark

> 📅 最終更新日: 2026/08/26

`benchmark/util_benchmark.py` は実行器とタスクグラフのパフォーマンスベンチマークテスト機能を提供し、異なる実行モードのパフォーマンス差異を比較します。

## 設計目的

実際のプロジェクトでは、適切な実行モードの選択がパフォーマンスにとって極めて重要です。ベンチマークテストツールは以下を実現します:
- 異なる実行モードの実行時間を比較
- 並列化効果を検証
- パフォーマンスボトルネックを発見

## 主要関数

### benchmark_executor

`TaskExecutor` のベンチマークテストを行います。

```python
async def benchmark_executor(
    sync_executor: TaskExecutor[Any, Any],
    async_executor: TaskExecutor[Any, Any],
    task_source: Iterable[Any],
    execution_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    実行器のベンチマークテストを行います。

    :param sync_executor: 同期実行器テンプレート（serial/thread execution_mode で使用）
    :param async_executor: 非同期実行器テンプレート（async execution_mode で使用）
    :param task_source: タスクソース。タスクリストを生成するために使用
    :param execution_modes: 実行モードのリスト、デフォルト ["serial", "thread", "async"]
    :return: テスト結果辞書（use_time, execution_modes, table を含む）
    """
```

テストフロー:
1. 実行器テンプレートをクローン（`async` モードは `async_executor` を、それ以外のモードは `sync_executor` をクローン）し、状態汚染を防止
2. `set_execution_mode(mode)` を呼び出して現在のテストモードを設定
3. `serial` / `thread` モード: `run(task_list)` を呼び出し（内部でタスク注入、終了シグナル注入、起動を実行）; `async` モード: `await run_async(task_list)` を呼び出し
4. 各モードの実行時間を記録し、`format_table` で時間テーブルを出力

出力例（`format_table` が生成するボーダー付きテーブル、単位は秒）:
```
+--------+--------+
| #      | Time   |
+--------+--------+
| serial | 2.3401 |
| thread | 0.8932 |
| async  | 0.6714 |
+--------+--------+
```

### benchmark_graph

`TaskGraph` のベンチマークテストを行います。

```python
async def benchmark_graph(
    sync_graph: TaskGraph,
    async_graph: TaskGraph,
    init_tasks_dict: Mapping[str, Iterable[Any]],
    graph_modes: list[str] | None = None,
    execution_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    タスクグラフのベンチマークテストを行います。

    :param sync_graph: 同期タスクグラフレプレート（serial/thread execution_mode で使用）
    :param async_graph: 非同期タスクグラフレプレート（async execution_mode で使用）
    :param init_tasks_dict: 初期タスク辞書、キーはタスクラベル、値はタスクリスト
    :param graph_modes: グラフ実行モードのリスト、デフォルト ["serial", "thread", "async"]
    :param execution_modes: 実行モードのリスト、デフォルト ["serial", "thread", "async"]
    :return: テスト結果辞書（use_time, table, graph_modes, execution_modes を含む）
    """
```

テストフロー:
1. `graph_modes` × `execution_modes` のすべての組み合わせをイテレート
2. タスクグラフをクローン（`execution_mode="async"` の場合は `async_graph` を、それ以外は `sync_graph` をクローン）
3. `set_graph_mode(graph_mode)` と `set_stage_execution_mode(execution_mode)` を呼び出し
4. `graph_mode="async"` の場合は `await run_async()` を実行; その他のグラフモードでは `run()` を実行。このうち `execution_mode="async"` の組み合わせは関数内部で `asyncio.to_thread(...)` により起動され、`benchmark_graph()` 自身のイベントループとの競合を回避
5. 実行時間を記録し、`format_table` で時間テーブルを出力

出力例（単位は秒）:
```
+-----------------+--------+--------+--------+
| graph/execution | serial | thread | async  |
+-----------------+--------+--------+--------+
| serial          | 5.2341 | 3.4512 | 3.2123 |
| thread          | 2.1234 | 1.8912 | 1.6543 |
| async           | 2.0534 | 1.7345 | 1.4234 |
+-----------------+--------+--------+--------+
```

## 使用例

### 実行器のテスト

```python
import asyncio
from celestialflow import TaskExecutor
from celestialflow.benchmark.util_benchmark import benchmark_executor


# 同期タスクを定義
def sync_task(x):
    return x * 2


# 非同期タスクを定義
async def async_task(x):
    await asyncio.sleep(0.01)
    return x * 2


# 実行器を作成
sync_executor = TaskExecutor("SyncBench", sync_task)
async_executor = TaskExecutor("AsyncBench", async_task)

# ベンチマークテストを実行
asyncio.run(
    benchmark_executor(
        sync_executor=sync_executor,
        async_executor=async_executor,
        task_source=range(1000),
        execution_modes=["serial", "thread", "async"],
    )
)
```

### タスクグラフのテスト

```python
import asyncio
from celestialflow import TaskGraph, TaskStage
from celestialflow.benchmark.util_benchmark import benchmark_graph


def process_a(x: int) -> int:
    return x * 2


def process_b(x: int) -> int:
    return x + 1


async def async_process_a(x: int) -> int:
    return x * 2


async def async_process_b(x: int) -> int:
    return x + 1


# 同期ノードを作成
stage_a = TaskStage("A", process_a)
stage_b = TaskStage("B", process_b)

# 非同期ノードを作成
async_stage_a = TaskStage("A", async_process_a)
async_stage_b = TaskStage("B", async_process_b)

# 同期グラフを構築
sync_graph = TaskGraph(name="SyncGraph")
sync_graph.set_stages(stages=[stage_a, stage_b])
sync_graph.connect([stage_a], [stage_b])

# 非同期グラフを構築
async_graph = TaskGraph(name="AsyncGraph")
async_graph.set_stages(stages=[async_stage_a, async_stage_b])
async_graph.connect([async_stage_a], [async_stage_b])

# ベンチマークテストを実行（benchmark_graph は async 関数なので await が必要）
asyncio.run(
    benchmark_graph(
        sync_graph=sync_graph,
        async_graph=async_graph,
        init_tasks_dict={stage_a.get_name(): range(100)},
    )
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

**Graph Mode（グラフモード）**:
- `serial`: ノードをメインスレッドで実行
- `thread`: ノードを独立スレッドで実行
- `async`: グラフがイベントループで統一的にディスパッチ; 同期ノードはスレッドにディスパッチ、非同期ノードはコルーチンで直接実行

**Execution Mode（実行モード）**:
- `serial`: ノード内部で逐次実行
- `thread`: ノード内部でスレッドプール実行
- `async`: ノード内部でコルーチン非同期実行

組み合わせ例:
| Graph \ Execution | serial | thread | async |
|-------------------|--------|--------|-------|
| serial | S-S | S-T | S-A |
| thread | T-S | T-T | T-A |
| async  | A-S | A-T | A-A |

## 出力情報

### 時間テーブル

各設定の実行時間を表示します。

### 戻り値

`benchmark_executor` は以下の内容を含む辞書を返します:
- `use_time`: 各モードの実行時間リスト（`execution_modes` と 1 対 1 に対応）
- `execution_modes`: テストされた実行モードのリスト
- `table`: フォーマット済み時間テーブル文字列

`benchmark_graph` は以下の内容を含む辞書を返します:
- `use_time`: `graph_modes × execution_modes` の実行時間マトリックス（行・列はテーブルと対応）
- `table`: フォーマット済み時間テーブル文字列
- `graph_modes`: テストされたグラフモードのリスト（テーブルの行に対応）
- `execution_modes`: テストされた実行モードのリスト（テーブルの列に対応）

## 注意事項

1. **クローン機構**: 各テストで元のオブジェクトをクローンし、状態汚染を防止
2. **タスク固定**: 全テストで同じタスクリストを使用し、公平性を確保
3. **リソース競合**: スレッドモードはリソース競合により結果が変動する可能性があります。複数回のテストを推奨
4. **非同期要件**: `benchmark_executor` と `benchmark_graph` はどちらも非同期関数であり、`await` または `asyncio.run` が必要
5. **テンプレートの分離**: `benchmark_executor` と `benchmark_graph` はどちらも同期/非同期テンプレートをそれぞれ別に提供する必要があります。`execution_mode="async"` には async 関数が必要なため
6. **マトリックスの完全性**: `benchmark_graph` の現在の実装はデフォルトで `serial/thread/async × serial/thread/async` の 9 通りの組み合わせをカバーします
