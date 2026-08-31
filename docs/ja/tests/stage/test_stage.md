# タスクステージテスト (test_stage.py)

> 📅 最終更新日: 2026/08/19

## 役割
`celestialflow.stage.core_stage` の `TaskStage` クラスを検証し、ノード設定、実行モード切り替え、および識別子管理がフレームワークの設計要件を満たしていることを確認します。

## コアテスト対象
- `TaskStage`: タスクグラフの基本論理ユニット。

## テストカバレッジマトリクス

### `TestTaskStageConfig` — ノード設定検証（8 ケース）

| ケース | カバレッジ目標 |
|------|----------|
| `test_stage_name_identity` | name が一意の識別子であること |
| `test_stage_name_changes_with_name` | `set_name()` 後に識別子が同期更新されること |
| `test_valid_execution_mode_serial` | `execution_mode="serial"` が合法であること |
| `test_valid_execution_mode_thread` | `execution_mode="thread"` が合法であること |
| `test_valid_execution_mode_async` | `execution_mode="async"` が合法であること |
| `test_invalid_execution_mode` | 不正な `execution_mode` が `InvalidOptionError` をスローすること |
| `test_summary_contains_execution_mode` | `get_summary()` に `execution_mode` フィールドが含まれること |
| `test_prev_binding_survives_execution_mode_switch` | `execution_mode` を切り替えても前駆バインディングのメトリクスが同期を保つこと |

### `TestTaskStageStartErrors` — 例外グループ収集（2 ケース）

| ケース | カバレッジ目標 |
|------|----------|
| `test_start_raises_exception_group_after_finish` | 同期 start が finish 後に収集された例外をまとめてスローすること |
| `test_start_async_raises_exception_group_after_finish` | 非同期 start_async が finish 後に例外をまとめてスローすること |

## テストの重点
- **設定の厳密性**: 初期化段階で不正な実行モードを確実に遮断し、不正モードが `InvalidOptionError` をスローすることを確認。
- **メタデータ同期**: グラフ参照キーとしての Stage 名の安定性と、`execution_mode` 切り替え後でも前駆バインディングが同期を保つことを検証。
- **例外グループ収集**: 同期/非同期 start のライフサイクル中、前置・後置の例外は `ExceptionGroup` としてまとめてスローされるべき。

## 実行方法

```bash
# すべて実行
pytest tests/stage/test_stage.py -v

# 識別子管理テストのみ実行
pytest tests/stage/test_stage.py -k "name" -v

# 実行モード検証テストのみ実行
pytest tests/stage/test_stage.py -k "mode" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|------|------|
| `TestTaskStageConfig` | ~0.2s（純粋な設定検証、タスク実行なし） |
| `TestTaskStageStartErrors` | ~0.3s（monkeypatch による例外注入を含む） |

## 重要な詳細
- `TaskStage` は直接タスクを実行せず、`TaskExecutor` の設定と `Queue` の管理を通じて動作を組織化します。
- `TestTaskStageStartErrors` は monkeypatch で `_prepare_start` と `_finish_start` に例外を注入し、例外グループ収集メカニズムを検証します。

## 注意事項
- タスクステージは TaskGraph を構成する基本要素です。
- 関連実装は `src/celestialflow/stage/core_stage.py` にあります。
