# Benchmark

> 📅 最終更新日: 2026/05/24

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
    実行器のベンチマークテストを行います。

    :param sync_executor: 同期実行器テンプレート
    :param async_executor: 非同期実行器テンプレート
    :param task_source: タスクソース
    :param sync_modes: 同期モードリスト。デフォルト ["serial", "thread"]
    :param async_modes: 非同期モードリスト。デフォルト ["async"]
    :return: テスト結果辞書（use_time, sync_modes, async_modes, table を含む）
    """
```

テストフロー：
1. 実行器をクローン（状態汚染を防止）
2. 各モードに対して実行方式を設定
3. タスクを実行し計時
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
    タスクグラフのベンチマークテストを行います。

    :param sync_graph: 同期タスクグラフテンプレート（serial/thread モード用）
    :param async_graph: 非同期タスクグラフテンプレート（async モード用）
    :param init_tasks_dict: 初期タスク辞書
    :param stage_modes: ノードモードリスト。デフォルト ["serial", "thread"]
    :param execution_sync_modes: 同期実行モードリスト。デフォルト ["serial", "thread"]
    :param execution_async_modes: 非同期実行モードリスト。デフォルト ["async"]
    :return: テスト結果辞書（table, stage_modes, sync_modes, async_modes を含む）
    """
```

テストフロー：
1. 各 `stage_mode` × `execution_mode` の組み合わせに対して
2. タスクグラフをクローン
3. `set_graph_mode(stage_mode, execution_mode)` を設定
4. `start_graph()` を実行し計時
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

# 同期ノードを作成
stage_a = TaskStage("A", process_a)
stage_b = TaskStage("B", process_b)

# 非同期ノードを作成
async_stage_a = TaskStage("A", async_process_a)
async_stage_b = TaskStage("B", async_process_b)

# 同期グラフを構築
sync_graph = TaskGraph()
sync_graph.set_stages(stages=[stage_a, stage_b])
sync_graph.connect([stage_a], [stage_b])

# 非同期グラフを構築
async_graph = TaskGraph()
async_graph.set_stages(stages=[async_stage_a, async_stage_b])
async_graph.connect([async_stage_a], [async_stage_b])

# ベンチマークテストを実行
benchmark_graph(
    sync_graph=sync_graph,
    async_graph=async_graph,
    init_tasks_dict={stage_a.get_tag(): range(100)},
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
