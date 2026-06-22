# 特殊化ステージテスト (test_stages.py)

> 📅 最終更新日: 2026/06/22

## 役割
`celestialflow.stage.core_stages` の特殊化タスクノード（Splitter、Router）の機能を検証し、タスクが正しく分割・ルーティング・分配されることを確認します。

## コアテスト対象
- `TaskSplitter`: 単一タスクの結果を複数のサブタスクに分割するノード。
- `TaskRouter`: 事前定義されたルールに基づいてタスクを特定の下流ノードに転送するルーター。

## 主要テストシナリオ

### `TestTaskSplitter` — タスクスプリッター
| ケース | カバレッジ目標 |
|------|----------|
| `test_splitter_init` | デフォルト直列モード、リトライなし、初期カウンタが 0 であることを検証 |
| `test_splitter_process_success` | `TaskGraph` 内で正常実行後、下流が 3 つの独立タスクを受信し、`split_counter` のカウントが正しいことを検証 |
| `test_splitter_allows_empty_iterable` | 空のイテラブル入力が 0 個のサブタスクを生成し、例外をスローしないことを検証 |
| `test_splitter_supports_generator_input` | 1 回限りのイテレータ（generator）入力でも正しく分割し、すべてのサブタスクを分配できることを検証 |
| `test_splitter_allows_constructor_split_item` | `split_item` コンストラクタパラメータで単一サブタスクの変換ロジックを注入できることを検証 |

### `TestTaskRouter` — タスクルーター
| ケース | カバレッジ目標 |
|------|----------|
| `test_router_init` | デフォルト直列モード、リトライなし、ルートカウンタが空辞書であることを検証 |
| `test_router_route_logic` | `_route` が構築時に渡されたルート関数を呼び出し、`(target, task)` 結果を返すことを検証。未知の target が `InvalidOptionError` をスローすることを検証 |
| `test_router_process_success` | `TaskGraph` 内で正常ルーティング後、`route_counters` のカウントが正しく、ターゲットノードがそれぞれ対応する数の成功タスクを受信することを検証 |
| `test_router_binding_counter_uses_stable_metrics_lock` | ルートカウンタが作成時から安定した metrics ロックに紐づいており、`execution_mode` を切り替えても同一のロックオブジェクトを保持することを検証 |

## テストの重点
- **1 対多の伝播**: Splitter の結果リストが同一結果のブロードキャストではなく、複数の独立したタスクエンベロープに展開されることを検証。
- **名前付き分配**: Router が内部ルート関数と事前バインディング機構を通じてタスクを指定された下流ノードに正確に誘導することを検証。
- **状態追跡**: 特殊化ノード内部のカスタムカウンタ（`split_counter`、`route_counters`）がビジネスロジックの実行状況を正確に反映することを検証。

## 実行方法

```bash
# すべて実行
pytest tests/stage/test_stages.py -v

# TaskSplitter テストのみ実行
pytest tests/stage/test_stages.py -k "splitter" -v

# TaskRouter テストのみ実行
pytest tests/stage/test_stages.py -k "router" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|------|------|
| `TestTaskSplitter` | ~0.2s |
| `TestTaskRouter` | ~0.2s |

## 重要な詳細
- テストは `TaskGraph.connect()` と `TaskGraph.start_graph()` を使用して実際のグラフ実行環境を構築して検証し、mock キューによる出力の傍受は行いません。
- 組み込みの `split_counter` と `route_counters` は特殊化 Stage の内部機構によって自動的に維持されます。

## 注意事項
- 特殊化ステージは複雑なワークフローにおけるデータ分岐と並列度の動的調整によく使用されます。
- 関連実装は `src/celestialflow/stage/core_stages.py` にあります。
