# 特定グラフ構造テスト (test_structure.py)

> 📅 最終更新日: 2026/08/26

## 役割
`TaskLoop` と `TaskWheel` の2つの事前定義循環グラフ構造の専用解析能力を検証し、ならびに各種事前定義グラフ構造（`TaskChain`、`TaskCross`、`TaskGrid`、`TaskLoop`、`TaskWheel`、`TaskComplete`）の入力検証を行い、空入力や不正入力で静的に構築されたりクラッシュが発生したりしないことを確認します。

## コアテスト対象
- `TaskLoop`: 単純な閉ループタスクチェーン。
- `TaskWheel`: 中心拡散型で循環を持つホイール構造。
- `TaskChain`, `TaskCross`, `TaskGrid`, `TaskComplete`: 事前定義グラフ構造の空/不正入力検証。

## テストカバレッジマトリックス

| テストクラス | ケース数 | カバレッジ対象 |
|------------|---------|--------------|
| `TestTaskLoop` | 2 | isDAG が False と識別、循環内ノード同層、ソースノード導出が代表点1つを返す |
| `TestTaskWheel` | 2 | Center が第0層、Ring が第1層、ソースノードが Center のみを返す |
| `TestStructureValidation` | 10 | 空 stages / 空 layers / 空グリッド / 先頭行空 / 行長不一致 / 単一ノード Complete / 各構造の空入力検証 |
| **合計** | **14** | |

## 主要テストフロー

### TaskLoop 解析
- `isDAG` が正しく `False` として識別されることを検証。
- 循環内の全ノードが同一の論理階層に割り当てられることを検証。
- ソースノード導出が循環から1つの代表点を注入点として選択できることを検証。

### TaskWheel 解析
- 中心ノード（Center）が第0層にあり、外側の循環ノード（Ring）が第1層にあることを検証。
- `get_source_names()` が Center ノードのみを返し、タスクが中心から注入されることを検証。

### 構造入力検証 (`TestStructureValidation`)
全 6 種類の事前定義グラフ構造に対する空/不正入力の境界をカバー：

| ケース | 検証ポイント |
|--------|------------|
| `test_chain_empty_stages_raises` | `TaskChain` の空 stages が `InvalidStructureError` をスロー |
| `test_cross_empty_layers_raises` | `TaskCross` の空 layers が `InvalidStructureError` をスロー |
| `test_cross_empty_layer_raises` | `TaskCross` の内部に空層を含む場合 `InvalidStructureError` をスロー |
| `test_grid_empty_raises` | `TaskGrid` の空グリッドが `InvalidStructureError` をスロー |
| `test_grid_empty_row_raises` | `TaskGrid` の先頭行が空の場合 `InvalidStructureError` をスロー |
| `test_grid_ragged_rows_raises` | `TaskGrid` の行長不一致が `InvalidStructureError` をスロー |
| `test_loop_empty_stages_raises` | `TaskLoop` の空 stages が `InvalidStructureError` をスロー |
| `test_wheel_empty_ring_raises` | `TaskWheel` の空 ring が `InvalidStructureError` をスロー |
| `test_complete_single_node_raises` | `TaskComplete` の単一ノードが `InvalidStructureError` をスロー |
| `test_complete_empty_stages_raises` | `TaskComplete` の空 stages が `InvalidStructureError` をスロー |

## テストの重点
- **非 DAG 識別**: 循環構造が誤って DAG として処理されないことを確認。
- **階層の一貫性**: 循環依存が存在する場合でも、論理階層の区分が物理的直感に合致することを検証。
- **ソースノード特化**: 特定構造向けに最適化されたソースノード検索ロジック。
- **境界検証**: すべての事前定義グラフ構造が空/不正入力を厳密に拒否し、空グラフを静的に構築したりしないことを確認。

## 実行方法

```bash
# 全部実行
pytest tests/graph/test_structure.py -v

# TaskLoop テストのみ
pytest tests/graph/test_structure.py::TestTaskLoop -v

# TaskWheel テストのみ
pytest tests/graph/test_structure.py::TestTaskWheel -v

# 入力検証テストのみ
pytest tests/graph/test_structure.py::TestStructureValidation -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|---------|
| `TestTaskLoop` | ~1s（グラフ起動と終了を含む） |
| `TestTaskWheel` | ~1s |
| `TestStructureValidation` | < 0.1s（純粋な構築検証） |

## 重要な詳細
- `TaskLoop` は `run()` で起動しタスクを注入します（`run` のデフォルトは `if_put_signal=True` で、ソースノードに終了シグナルを自動補完してテストの終了を保証）。
- `TaskWheel` はタスクを実行しません。`set_graph_mode()` と `set_stage_execution_mode()` で設定した後、`get_graph_analysis()` / `get_source_names()` を直接呼び出して静的解析を行います。
- テストの重点は「実行結果」ではなく「解析結果」（analysis dict）にあります。
- 入力検証テストはすべて純粋な構築操作であり、グラフの起動を伴いません。

## 注意事項
- 本テストは `TaskGraph` サブクラスの特化動作に焦点を当てています。
- 関連実装は `src/celestialflow/graph/core_structure.py` にあります。
