# 特定グラフ構造テスト (test_structure.py)

> 📅 最終更新日: 2026/05/23

## 役割
`TaskLoop` と `TaskWheel` の2つの事前定義循環グラフ構造の専用解析能力を検証し、非 DAG シナリオでの動作が期待通りであることを確認します。

## コアテスト対象
- `TaskLoop`: 単純な閉ループタスクチェーン。
- `TaskWheel`: 中心拡散型で循環を持つホイール構造。

## 主要テストフロー
1. **TaskLoop 解析**:
   - `isDAG` が正しく `False` として識別されることを検証。
   - 循環内の全ノードが同一の論理階層に割り当てられることを検証。
   - ソースノード導出が循環から1つの代表点を注入点として選択できることを検証。
2. **TaskWheel 解析**:
   - 中心ノード（Center）が第0層にあり、外側の循環ノード（Ring）が第1層にあることを検証。
   - `get_source_stages` が Center ノードのみを返し、タスクが中心から注入されることを検証。

## テストの重点
- **非 DAG 識別**: 循環構造が誤って DAG として処理されないことを確認。
- **階層の一貫性**: 循環依存が存在する場合でも、論理階層の区分が物理的直感に合致することを検証。
- **ソースノード特化**: 特定構造向けに最適化されたソースノード検索ロジック。

## 実行方法

```bash
# 全テスト実行
pytest tests/graph/test_structure.py -v

# TaskLoop テストのみ
pytest tests/graph/test_structure.py::TestTaskLoop -v

# TaskWheel テストのみ
pytest tests/graph/test_structure.py::TestTaskWheel -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|---------|
| `TestTaskLoop` | ~1s（グラフ起動と終了を含む） |
| `TestTaskWheel` | ~1s |

## 重要な詳細
- `start_loop` や `start_wheel` などの特化メソッドを使用してテストを起動し、`put_termination_signal=True` を併用。
- テストの重点は「実行結果」ではなく「解析結果」（analysis dict）にあります。

## 注意事項
- 本テストは `TaskGraph` サブクラスの特化動作に焦点を当てています。
- 関連実装は `src/celestialflow/graph/core_structure.py` にあります。
