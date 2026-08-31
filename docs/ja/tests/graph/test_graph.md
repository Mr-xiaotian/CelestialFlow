# タスクグラフコア機能テスト (test_graph.py)

> 📅 最終更新日: 2026/08/31

## 役割
`TaskGraph` およびその各種トポロジサブクラス（`TaskChain`、`TaskCross`、`TaskGrid`）のコア機能を包括的に検証し、同期/非同期実行、エラー伝播、トポロジ解析、実行モードマトリクス、ソースノード導出、循環グラフ動作、終了段階の安全検査、ランタイムスナップショット収集をカバーします。

## コアテスト対象
- `TaskGraph`: 汎用タスクグラフコンテナ
- `TaskChain`, `TaskCross`, `TaskGrid`: 事前定義トポロジ構造
- `TaskStage`: グラフノード定義

## テスト範囲

### 集計表

| テストクラス | ケース数 | カバレッジポイント |
|-------------|---------|------------------|
| `TestTaskGraphBasic` | 10 | set_ctree による既存 stage の更新、未知 stage 名検索例外、2ノード DAG、ファンアウト、ファンイン、エラー伝播、DB リプレイ、DB エラータイプフィルタリプレイ、DB での pending 保持、finish 後の例外グループ一括送出 |
| `TestTaskGraphAsync` | 6 | async モード 2ノード、ファンアウト、ファンイン、エラー伝播、async execution_mode、async finish 後の例外グループ一括送出 |
| `TestTaskGraphStructure` | 3 | Chain、Cross、Grid 構造 |
| `TestTaskGraphAnalysis` | 4 | ゲッターのオンデマンド構築、構造変更後の自動再構築、DAG 検出、階層計算 |
| `TestTaskGraphRuntimeSnapshot` | 1 | Reporter スナップショット収集の未起動 Stage に対する耐障害性 |
| `TestStageExecutionMatrix` | 7 | serial/thread/async graph_mode × serial/thread/async execution_mode |
| `TestTaskGraphThread` | 6 | thread モード 2ノード、ファンアウト、ファンイン、エラー伝播、lambda、staged スケジューリング |
| `TestSourceStages` | 5 | 線形グラフ source、ファンイン source、ダイヤモンドグラフ source、単一ソース SCC 代表点、複数ソース SCC 各1点 |
| `TestCyclicGraph` | 3 | serial モード循環グラフ警告、循環グラフ isDAG 検出、循環内同層 + 尾の階層 |
| **合計** | **45** | |

> **説明**: ここでの統計は `test_graph.py` 内のテストクラスです。`TaskLoop` と `TaskWheel` の専用テストは `test_structure.py` にあります。

### 主要テストフロー

#### 基本トポロジ実行
```mermaid
graph LR
    A[stage1<br/>add_one] -->|fan-out| B[stage2<br/>double]
    A -->|fan-out| C[stage3<br/>to_str]
    B -->|fan-in| D[merge<br/>add_one]
    C -->|fan-in| D
```

- **2ノード DAG** (`test_graph_dag_two_nodes`): A→B のデータフローが正しく、2ノードがそれぞれ3つ成功することを検証。
- **ファンアウト** (`test_graph_fan_out`): 1つの上流が複数の下流に分配され、sink_a と sink_b がそれぞれ2つ成功することを検証。
- **ファンイン** (`test_graph_fan_in`): 複数の上流が1つの下流に集約され、merge ノードが4つのタスクを受け取ることを検証。
- **エラー伝播** (`test_graph_error_propagation`): `50` が `ValueError` をトリガーしてもフローが中断されず、下流が成功タスクのみを受け取ることを検証。
- **DB 起動** (`test_graph_restore_db`): SQLite から failed/pending タスクをリプレイすることを検証。
- **DB 起動フィルタリング** (`test_graph_restore_db_filters_error_type_when_enabled`): 各 stage の `retry_exceptions` に基づいてリプレイタスクをフィルタリングすることを検証。
- **DB で pending を保持** (`test_graph_restore_db_filter_keeps_pending_records`): フィルタ有効時、pending レコードのリプレイが継続されることを検証。
- **未知 stage 名例外** (`test_graph_stage_lookup_unknown_stage_raises`): stage を明示指定してタスク注入する際、存在しない stage 名は `NodeNotFoundError` をスローすべき。
- **set_ctree で既存 stage を更新** (`test_set_ctree_updates_existing_stages`): 先に `set_stages` を呼んだ後で `set_ctree` を呼ぶ場合、既存 stage も同じイベントクライアントを共有すべき。
- **finish 後の例外グループ一括送出** (`test_start_raises_exception_group_after_finish`): 同期 `start` が finish 後に収集された例外を一括送出することを検証。

#### 非同期と並行
- async モードの2ノード、ファンアウト、ファンイン、エラー伝播は同期モードとセマンティクスが一致。
- `test_graph_async_execution_mode`: `graph_mode="async"` + `execution_mode="async"` の組み合わせを検証。
- `test_start_async_raises_exception_group_after_finish`: 非同期 `start_async` が finish 後に例外グループを一括送出することを検証。

#### 実行モードマトリクス (`TestStageExecutionMatrix`)
`graph_mode` × `execution_mode` の全 **7 組み合わせ**をカバー：

| ケース | graph_mode | execution_mode |
|--------|-----------|----------------|
| `test_serial_serial` | serial | serial |
| `test_serial_thread` | serial | thread |
| `test_thread_serial` | thread | serial |
| `test_thread_thread` | thread | thread |
| `test_async_serial` | async | serial |
| `test_async_thread` | async | thread |
| `test_async_async` | async | async |

各ケースは5つの入力タスクを持つ2ノード DAG を使用し、2つの stage がそれぞれ5つ成功することを検証。

#### グラフ構造解析 (`TestTaskGraphAnalysis`)
- **オンデマンド構築** (`test_getters_build_analysis_on_demand`): 解析と構造のゲッターは明示的に build しなくても直接利用可能なはず。
- **キャッシュ自動再構築** (`test_getters_refresh_analysis_after_connect`): 構造変更後、ゲッターは解析キャッシュを自動的に再構築すべき。
- **DAG 検出** (`test_dag_detection`): `isDAG` フラグがグラフに循環があるかどうかを正しく反映。
- **階層計算** (`test_layer_computation`): 線形チェーン A→B→C のトポロジ階層が {A:0, B:1, C:2} であることを検証。

#### 終了とスナップショット
- **終了例外グループ** (`test_start_raises_exception_group_after_finish`): 同期 `start` が finish 後に ExceptionGroup を一括送出することを検証。
- **スナップショット耐障害性** (`TestTaskGraphRuntimeSnapshot`): ノード未起動（`start_time` なし）時に Reporter がスナップショット収集してもクラッシュしないことを検証。

#### 複雑な構造 (`TestTaskGraphStructure`)
| 構造 | ノード数 | スレッド数 | カバーシナリオ |
|------|---------|-----------|--------------|
| Chain | 3 チェーン | 3 | 線形パイプライン |
| Cross | 2×3 グリッド | 4 | 全結合クロス |
| Grid | 2×2 グリッド | 4 | グリッド状結合 |

#### スレッドモード (`TestTaskGraphThread`)
`graph_mode="thread"` における fan-out、fan-in、エラー伝播、lambda 関数サポート、staged スケジューリングを検証。

#### ソースノード導出 (`TestSourceStages`)
5つのケースで以下のシナリオをカバー：

| ケース | トポロジ | 期待される result |
|--------|---------|------------------|
| `test_source_stages_linear` | A→B→C | [A] |
| `test_source_stages_fan_in` | A→C, B→C | [A, B] |
| `test_source_stages_diamond` | A→{B,C}→D | [A] |
| `test_source_stages_cycle_returns_one_source_scc_member` | s1→s2→s3→s1 | 循環内の代表点1つ |
| `test_source_stages_returns_one_member_per_source_scc` | 2つの交わらない循環が s5 に集約 | 各ソース SCC から代表点1つずつ |

#### 循環グラフ (`TestCyclicGraph`)
| ケース | 検証ポイント |
|--------|------------|
| `test_cyclic_serial_graph_raises` | serial graph_mode 時に `get_source_names()` を呼ぶと循環グラフは `ConfigurationError` をスローすべき（`"TaskGraph contains a cycle while graph_mode='serial'"` にマッチ） |
| `test_cyclic_is_dag_false` | s1→s2→s3→s1 の `isDAG` が `False` であること |
| `test_cyclic_layers` | 循環内ノード (s1,s2,s3) が同層、尾の s4 が循環階層 + 1 |

### ランタイムスナップショット
`collect_runtime_snapshot()` が書き込むスナップショットデータは `TaskGraph.status_dict` に保存され、Reporter などのコンポーネントから読み取り可能です。

## 重要な詳細

### 終了信号の動作
- 循環グラフは `run()` で起動しタスクを注入します（`run` のデフォルトは `if_put_signal=True` で、ソースノードに終了シグナルを自動補完してテストの終了を保証）。
- serial graph_mode 時に循環グラフで `get_source_names()` を呼ぶと `ConfigurationError` がトリガーされます（`test_cyclic_serial_graph_raises` 参照）。

### Lambda サポート
スレッドモードでは lambda をタスク関数として使用可能（`test_graph_thread_with_lambda`）。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `celestialflow` | `TaskGraph`, `TaskChain`, `TaskCross`, `TaskGrid`, `TaskStage` |

## 実行方法

```bash
# 全部実行
pytest tests/graph/test_graph.py -v

# 構造テストのみ（最も時間がかかる、マルチスレッド含む）
pytest tests/graph/test_graph.py::TestTaskGraphStructure -v

# 解析テストのみ（最速、タスク実行なし）
pytest tests/graph/test_graph.py::TestTaskGraphAnalysis -v
```

## パフォーマンス参考

| テスト | 所要時間（Windows / i5） |
|--------|------------------------|
| `TestTaskGraphBasic` | ~2s |
| `TestTaskGraphAsync` | ~3s |
| `TestTaskGraphStructure` | ~5s |
| `TestTaskGraphAnalysis` | ~1s |
| `TestTaskGraphRuntimeSnapshot` | < 0.1s |
| `TestStageExecutionMatrix` | ~5s |
| `TestTaskGraphThread` | ~4s |
| `TestSourceStages` | ~2s |
| `TestCyclicGraph` | ~2s |

## 関連ファイル

- `src/celestialflow/graph/core_graph.py`: `TaskGraph` 実装
- `src/celestialflow/graph/core_structure.py`: グラフ構造サブクラス
- `tests/graph/test_structure.py`: TaskLoop / TaskWheel 専用テスト
