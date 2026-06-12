# タスクステージテスト (test_stage.py)

> 📅 最終更新日: 2026/06/11

## 役割
`celestialflow.stage.core_stage` の `TaskStage` クラスを検証し、ノード設定、実行モード切り替え、および識別子管理がフレームワークの設計要件を満たしていることを確認します。

## コアテスト対象
- `TaskStage`: タスクグラフの基本論理ユニット。

## テストカバレッジマトリクス

| ケース | カバレッジ目標 |
|------|----------|
| `test_stage_name_identity` | name が一意の識別子であること |
| `test_stage_name_changes_with_name` | `set_name()` 後に識別子が同期更新されること |
| `test_valid_stage_mode_serial` | `stage_mode="serial"` が合法であること |
| `test_valid_stage_mode_thread` | `stage_mode="thread"` が合法であること |
| `test_invalid_stage_mode` | 不正な `stage_mode` が `StageModeError` をスローすること |
| `test_valid_execution_mode_serial` | `execution_mode="serial"` が合法であること |
| `test_valid_execution_mode_thread` | `execution_mode="thread"` が合法であること |
| `test_valid_execution_mode_async` | `execution_mode="async"` が合法であること |
| `test_invalid_execution_mode` | 不正な `execution_mode` が `ExecutionModeError` をスローすること |
| `test_summary_contains_stage_mode` | `get_summary()` に `stage_mode` と `execution_mode` が含まれること |
| `test_lambda_allowed_in_thread` | thread モードで lambda 関数が許可されること |

## テストの重点
- **設定の厳密性**: 初期化段階で不正なモード組み合わせを確実に遮断できることを確認。
- **メタデータ同期**: グラフ参照キーとしての Stage 名の安定性を検証。
- **モードセマンティクス**: 「ノード分離モード (Stage Mode)」と「タスク実行モード (Execution Mode)」の異なる責務を区別。

## 実行方法

```bash
# すべて実行
pytest tests/stage/test_stage.py -v

# 識別子管理テストのみ実行
pytest tests/stage/test_stage.py -k "name" -v

# モード検証テストのみ実行
pytest tests/stage/test_stage.py -k "mode" -v

# Lambda サポートテストのみ実行
pytest tests/stage/test_stage.py -k "lambda" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|------|------|
| `TestTaskStageConfig` | ~0.2s（純粋な設定検証、タスク実行なし） |

## 重要な詳細
- `TaskStage` は直接タスクを実行せず、`TaskExecutor` の設定と `Queue` の管理を通じて動作を組織化します。
- `test_lambda_allowed_in_thread` はスレッド分離モードにおけるタスク関数の柔軟性の重要な検証です。

## 注意事項
- タスクステージは TaskGraph を構成する基本要素です。
- 関連実装は `src/celestialflow/stage/core_stage.py` にあります。
