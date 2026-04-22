# test_graph.py テスト説明

> 📅 最終更新日: 2026/04/22

## テスト目的

`TaskGraph` およびそのサブクラス（`TaskChain`、`TaskCross`、`TaskGrid`、`TaskComplete`）を複数のグラフ構造で検証します。以下を含みます：
- DAG データフローの構築と実行
- ファンアウト（fan-out）、ファンイン（fan-in）、エラー伝播
- グラフ構造分析（DAG 検出、レイヤー計算）
- ランタイムサマリー統計

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestTaskGraphBasic` | 4 | 2ノード DAG、ファンアウト、ファンイン、エラー伝播 |
| `TestTaskGraphStructure` | 4 | Chain、Cross、Grid、Complete 構造 |
| `TestTaskGraphAnalysis` | 2 | DAG 検出、レイヤー計算 |
| `TestTaskGraphSummary` | 1 | サマリー統計 |

### 主要テストケースの詳細

#### `test_graph_dag_two_nodes`
- **目的**：最小の DAG（A -> B）のデータフローの正確性を検証します。
- **アサーション**：`stage1` が3件成功、`stage2` が3件成功（結果が正しく伝播）。

#### `test_graph_fan_out`
- **目的**：1つの上流ノードが複数の下流ノードに分配することを検証します。
- **アサーション**：source 2件、sink_a 2件、sink_b 2件。

#### `test_graph_fan_in`
- **目的**：複数の上流ノードが1つの下流ノードに集約することを検証します。
- **アサーション**：merge ノードが4件のタスクを受信（2 + 2）。

#### `test_graph_error_propagation`
- **目的**：エラータスクが全体のフローをブロックせず、下流に伝播しないことを検証します。
- **設計**：`stage1` が `[1, 50, 2]` を処理し、`50` が `ValueError` をトリガーします。
- **アサーション**：`stage1` が2件成功、1件失敗。`stage2` は成功した2件のタスクのみを受信。

#### `test_complete_structure`
- **目的**：完全グラフ（非 DAG）の基本的な起動と構造検出を検証します。
- **注意**：完全グラフで終了シグナルが自動注入されると `RuntimeWarning` がトリガーされ、ノードが早期に終了する可能性があります。テストは `isDAG == False` であることと、各ノードが少なくとも自身の入力を処理したことのみを検証します。

#### `test_layer_computation`
- **目的**：DAG のトポロジカルレイヤー計算が正しいことを検証します。
- **設計**：A -> B -> C の3層チェーン。
- **アサーション**：A がレイヤー0、B がレイヤー1、C がレイヤー2。

#### `test_graph_summary_counts`
- **目的**：`collect_runtime_snapshot()` が生成するサマリー統計が正確であることを検証します。
- **注意**：このテストでは `TaskReporter` は有効化されていません。サマリーを生成するには `collect_runtime_snapshot()` を**手動で呼び出す**必要があります。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `celestialflow` | `TaskGraph`、`TaskChain`、`TaskCross`、`TaskGrid`、`TaskComplete`、`TaskStage` |

## 発生しうる問題と注意事項

### 1. マルチプロセスモードでのタイムアウトリスク
`TaskCross`、`TaskGrid`、`TaskComplete` のデフォルト `stage_mode` は `"process"` です。Windows では各 `multiprocessing.Process` の起動に約100〜300msかかります。大きなグリッド（例：4x4）の場合、合計起動時間がテストのタイムアウト閾値を超える可能性があります。

**現在のテスト規模**：
- `test_cross_structure`：2x3 グリッド、4プロセス
- `test_grid_structure`：2x2 グリッド、4プロセス
- `test_complete_structure`：3ノード、3プロセス

これらの規模は180秒のタイムアウト内で安定して合格します。

### 2. 非 DAG グラフの終了シグナル動作
`TaskComplete`、`TaskLoop`、`TaskWheel` などの循環構造は `put_termination_signal=True` の場合にフレームワーク警告をトリガーします：
```
RuntimeWarning: Early injection of termination signals in a non-DAG graph ...
```

これは eager モードではノードが終了シグナルを受信すると即座にシャットダウンする可能性があり、他のノードからのタスクがまだキューに残っている場合があるためです。現在のテストではこの動作に対応するため、アサーションを正確な値ではなく `>= 1` に調整しています。

**推奨事項**：循環グラフでタスク数を正確にテストするには：
1. `put_termination_signal=False` を使用する
2. Web インターフェースまたは外部から終了シグナルを注入する
3. staged モードで実行する（循環グラフは staged モードをサポートしません）

### 3. `collect_runtime_snapshot` の手動呼び出し
`get_graph_summary()` が返すデータは最後の `collect_runtime_snapshot()` のスナップショットから取得されます。本番運用では `TaskReporter` が定期的に自動呼び出ししますが、単体テスト（reporter が有効化されていない場合）では手動で呼び出す必要があります。

この呼び出しを省略すると、`get_graph_summary()` は空の辞書または古いデータを返します。

### 4. `stage_mode="process"` と Pickle
`stage_mode="process"` を使用するすべてのテストでは、タスク関数と引数が pickle 可能である必要があります。現在のテストではトップレベル関数と基本型を使用しているため、この問題はありません。

### 5. Windows のプロセス spawn オーバーヘッド
Windows はデフォルトで `spawn` 方式を使用してプロセスを作成します（Linux/macOS は `fork`）。`spawn` はメインモジュールを再インポートするため、`if __name__ == "__main__":` ガードが適切に設定されていない場合、プロセスの再帰的な作成が発生する可能性があります。

**現在のテスト**：すべてのプロセス作成は `TaskGraph.start_graph()` 内部で管理されており、追加のガードは不要です。

## 実行方法

```bash
# すべて実行
pytest tests/test_graph.py -v

# 構造テストのみ（最も時間がかかる、マルチプロセスを含む）
pytest tests/test_graph.py::TestTaskGraphStructure -v

# 分析テストのみ（最速、タスク実行なし）
pytest tests/test_graph.py::TestTaskGraphAnalysis -v
```

## パフォーマンス参考値

| テスト | 所要時間（Windows / i5） |
|-------|------------------------|
| `TestTaskGraphBasic` | 約2秒 |
| `TestTaskGraphStructure` | 約5秒 |
| `TestTaskGraphAnalysis` | 約1秒 |
| `TestTaskGraphSummary` | 約1秒 |

## 関連ファイル

- `src/celestialflow/graph/core_graph.py`：`TaskGraph` の実装
- `src/celestialflow/graph/core_structure.py`：グラフ構造サブクラス
- `tests/demo_structure.py`：より複雑なグラフ構造のデモ（循環グラフ、多層ネットワークを含む）
