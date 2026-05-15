# test_graph.py テスト説明

> 📅 最終更新日: 2026/05/15

## テスト目的

複数のグラフ構造における `TaskGraph` およびそのサブクラス（`TaskChain`、`TaskCross`、`TaskGrid`、`TaskComplete`）の正確性を検証します。以下を含みます：
- DAG データフローの構築と実行
- ファンアウト（fan-out）、ファンイン（fan-in）、エラー伝播
- async モードおよび thread モードでのグラフ実行
- stage_mode × execution_mode マトリックス組み合わせ
- グラフ構造分析（DAG 検出、レベル計算）
- ソースノードの自動推論
- 循環グラフの動作
- ランタイムサマリー統計

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestTaskGraphBasic` | 4 | 2ノード DAG、ファンアウト、ファンイン、エラー伝播 |
| `TestTaskGraphAsync` | 5 | async モード2ノード、ファンアウト、ファンイン、エラー伝播、async+thread stage_mode |
| `TestTaskGraphStructure` | 4 | Chain、Cross、Grid、Complete 構造 |
| `TestTaskGraphAnalysis` | 2 | DAG 検出、レベル計算 |
| `TestTaskGraphSummary` | 1 | サマリー統計 |
| `TestStageExecutionMatrix` | 6 | serial/thread stage_mode × serial/thread/async execution_mode |
| `TestTaskGraphThread` | 6 | thread モード2ノード、ファンアウト、ファンイン、エラー伝播、lambda、staged スケジューリング |
| `TestSourceStages` | 3 | 線形グラフ source、ファンイン source、菱形グラフ source |
| `TestCyclicGraph` | 2 | 循環グラフ isDAG 検出、サイクル内同レベル+テールレベル |

### 主要テストケースの詳細

#### `test_graph_dag_two_nodes`
- **目的**: 最もシンプルな DAG（A → B）のデータフローの正確性。
- **アサーション**: `stage1` が3回成功、`stage2` が3回成功（結果が正しく伝播）。

#### `test_graph_fan_out`
- **目的**: 1つの上流ノードが複数の下流ノードに分配。
- **アサーション**: source 2、sink_a 2、sink_b 2。

#### `test_graph_fan_in`
- **目的**: 複数の上流ノードが1つの下流ノードに収束。
- **アサーション**: merge ノードが4タスク（2 + 2）を受信。

#### `test_graph_error_propagation`
- **目的**: エラータスクが全体のフローをブロックせず、下流に伝播しないことを検証。
- **設計**: `stage1` が `[1, 50, 2]` を処理、`50` が `ValueError` をトリガー。
- **アサーション**: `stage1` 成功2、失敗1；`stage2` は成功した2タスクのみ受信。

#### `test_complete_structure`
- **目的**: 完全グラフ（非 DAG）の基本的な起動と構造検出。
- **注意**: 完全グラフの終了信号自動注入は `RuntimeWarning` をトリガーし、ノードが早期に閉じる可能性があります。テストは `isDAG == False` と各ノードが少なくとも自身の入力を処理したことのみを検証。

#### `test_layer_computation`
- **目的**: DAG のトポロジカルレベル計算の正確性。
- **設計**: A → B → C 3層チェーン。
- **アサーション**: A がレベル0、B がレベル1、C がレベル2。

#### `test_graph_summary_counts`
- **目的**: `collect_runtime_snapshot()` で生成されるサマリー統計の正確性。
- **注意**: テストでは `TaskReporter` を有効にしていないため、サマリーを生成するには `collect_runtime_snapshot()` を**手動で呼び出す**必要があります。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `celestialflow` | `TaskGraph`、`TaskChain`、`TaskCross`、`TaskGrid`、`TaskComplete`、`TaskStage` |

## 起こりうる問題と注意事項

### 1. スレッドモードでのタイムアウトリスク
`TaskCross`、`TaskGrid`、`TaskComplete` のデフォルト `stage_mode` は `"thread"` です。グリッドが大きい場合、スレッドの起動とスケジューリングのオーバーヘッドがテストタイムアウト閾値を超える可能性があります。

**現在のテスト規模**:
- `test_cross_structure`: 2×3 グリッド、4スレッド
- `test_grid_structure`: 2×2 グリッド、4スレッド
- `test_complete_structure`: 3ノード、3スレッド

上記の規模は180秒のタイムアウト内で安定して通過します。

### 2. 非 DAG グラフの終了信号の動作
`TaskComplete`、`TaskLoop`、`TaskWheel` などの循環構造は、`put_termination_signal=True` の場合にフレームワーク警告をトリガーします：
```
RuntimeWarning: Early injection of termination signals in a non-DAG graph ...
```

これは eager モードでノードが終了信号を受信すると即座にシャットダウンする可能性がある一方、他のノードからの後続タスクがまだキューに残っている場合に発生します。現在のテストではこの動作に対応するため、アサーションを正確な値ではなく `>= 1` に調整しています。

**推奨**: 循環グラフで正確なタスクカウントをテストする場合：
1. `put_termination_signal=False` を使用
2. Web インターフェースまたは外部から終了信号を注入
3. staged モードで実行（循環グラフは staged モードをサポートしません）

### 3. `collect_runtime_snapshot` の手動呼び出し
`get_graph_summary()` が返すデータは、前回の `collect_runtime_snapshot()` のスナップショットに由来します。本番環境では `TaskReporter` が定期的に自動呼び出ししますが、ユニットテスト（reporter 未有効）では手動で呼び出す必要があります。

この呼び出しを省略すると、`get_graph_summary()` が空の辞書または古いデータを返します。

### `TestTaskGraphAsync` テストケースの詳細説明

#### `test_graph_async_two_nodes`
- **目的**: async モードでの2ノード DAG のデータフローの正確性。
- **アサーション**: `stage1` と `stage2` がそれぞれ3回成功。

#### `test_graph_async_fan_out`
- **目的**: async モードでのファンアウト構造（1つの上流から複数の下流）。

#### `test_graph_async_fan_in`
- **目的**: async モードでのファンイン構造（複数の上流が1つの下流に収束）。
- **アサーション**: merge ノードが4タスクを受信。

#### `test_graph_async_error_propagation`
- **目的**: async モードでエラータスクが全体のフローをブロックしないことを検証。

#### `test_graph_async_thread_stage_mode`
- **目的**: `stage_mode="thread"` + `execution_mode="async"` の組み合わせでの正しい実行。

### `TestStageExecutionMatrix` テストケースの詳細説明

`stage_mode`（serial/thread）× `execution_mode`（serial/thread/async）の全6組み合わせをカバー：

| テストケース | stage_mode | execution_mode |
|-------------|-----------|----------------|
| `test_serial_serial` | serial | serial |
| `test_serial_thread` | serial | thread |
| `test_serial_async` | serial | async |
| `test_thread_serial` | thread | serial |
| `test_thread_thread` | thread | thread |
| `test_thread_async` | thread | async |

各テストケースは5入力タスクの2ノード DAG を使用し、両ステージがそれぞれ5回成功することを検証します。

### `TestTaskGraphThread` テストケースの詳細説明

#### `test_graph_thread_two_nodes`
- **目的**: thread stage_mode での2ノード DAG のデータフローの正確性。

#### `test_graph_thread_fan_out`
- **目的**: thread モードでのファンアウト構造。

#### `test_graph_thread_fan_in`
- **目的**: thread モードでのファンイン構造。

#### `test_graph_thread_error_propagation`
- **目的**: thread モードでエラータスクがフローをブロックしないことを検証。

#### `test_graph_thread_with_lambda`
- **目的**: thread モードで lambda 関数がタスク処理関数としてサポートされることを検証。

#### `test_graph_thread_staged_schedule`
- **目的**: thread モード + `schedule_mode="staged"` での正常動作。

### `TestSourceStages` テストケースの詳細説明

#### `test_source_stages_linear`
- **目的**: 線形グラフ（A → B → C）で source がヘッドノード A のみ。

#### `test_source_stages_fan_in`
- **目的**: 2つの入口が1点に収束し、source が2つの入口ノード。

#### `test_source_stages_diamond`
- **目的**: 菱形グラフ A → {B, C} → D で source が A のみ。

### `TestCyclicGraph` テストケースの詳細説明

#### `test_cyclic_isDAG_false`
- **目的**: 循環グラフ（s1 → s2 → s3 → s1）の `isDAG` が `False` であることを検証。
- **注意**: `put_termination_signal=True` でサイクルを終了。

#### `test_cyclic_layers`
- **目的**: サイクル内ノード（s1, s2, s3）が同レベル、テールノード s4 がサイクルレベル + 1。

### 4. タスク関数の要件
すべてのテストのタスク関数とパラメータはトップレベル関数と基本型を使用し、互換性を確保しています。

### 5. スレッド安全性
現在のテストでは、すべてのスレッド作成は `TaskGraph.start_graph()` 内部で管理されており、追加の保護は不要です。

## 実行方法

```bash
# 全テスト実行
pytest tests/test_graph.py -v

# 構造テストのみ（最も時間がかかる、マルチスレッド含む）
pytest tests/test_graph.py::TestTaskGraphStructure -v

# 分析テストのみ（最速、タスク実行なし）
pytest tests/test_graph.py::TestTaskGraphAnalysis -v
```

## パフォーマンス参考

| テスト | 所要時間（Windows / i5） |
|--------|------------------------|
| `TestTaskGraphBasic` | ~2s |
| `TestTaskGraphAsync` | ~3s |
| `TestTaskGraphStructure` | ~5s |
| `TestTaskGraphAnalysis` | ~1s |
| `TestTaskGraphSummary` | ~1s |
| `TestStageExecutionMatrix` | ~5s |
| `TestTaskGraphThread` | ~4s |
| `TestSourceStages` | ~2s |
| `TestCyclicGraph` | ~2s |

## 関連ファイル

- `src/celestialflow/graph/core_graph.py`: `TaskGraph` 実装
- `src/celestialflow/graph/core_structure.py`: グラフ構造サブクラス
- `tests/demo_structure.py`: より複雑なグラフ構造デモ（循環グラフ、多層ネットワークを含む）
