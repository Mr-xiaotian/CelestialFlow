# ランタイム例外テスト (test_errors.py)

> 📅 最終更新日: 2026/06/11

## 役割
`celestialflow.runtime.util_errors` のカスタム例外体系を検証し、例外の継承関係、デフォルトメッセージ、追加フィールドが期待通りであることを確認します。

## カバレッジポイント
- 基本例外：`CelestialFlowError`、`ConfigurationError`、`RuntimeStateError`、`CelestialFlowTimeoutError`（`TimeoutError` も同時に継承）。
- オプションエラー：`InvalidOptionError`、`ExecutionModeError`、`StageModeError`、`ScheduleModeError`、`LogLevelError`、および各フィールド（`field`、`value`、`allowed`）。
- グラフ構造エラー：`GraphStructureError`、`DuplicateNodeError`、`UnknownNodeError`。
- ランタイムとライフサイクル：`RuntimeStateError`、`InitializationError`、`UnconsumedError`。
- タスクとロジック：`TaskFormatError`、`TerminationMergeError`。
- 外部依存：`ReporterError`、`RemoteWorkerError`、`CelestialTreeConnectionError`（デフォルトメッセージとカスタムメッセージをサポート）。

## テストカバレッジマトリクス

| 分類 | ケース数 | カバーする例外 |
|------|---------|--------------|
| 基本例外 | 1 | `CelestialFlowError` |
| 設定とオプション | 8 | `ConfigurationError`、`InvalidOptionError`（カスタムプレフィックス含む）、`ExecutionModeError`（カスタムモード含む）、`StageModeError`、`LogLevelError`、`ScheduleModeError` |
| グラフ構造 | 3 | `GraphStructureError`、`DuplicateNodeError`、`UnknownNodeError` |
| ランタイムとライフサイクル | 4 | `RuntimeStateError`、`InitializationError`、`CelestialFlowTimeoutError`、`UnconsumedError` |
| 外部サービスと通信 | 3 | `RemoteWorkerError`、`ReporterError`、`CelestialTreeConnectionError`（デフォルト/カスタムメッセージ） |
| タスクとロジック | 2 | `TaskFormatError`、`TerminationMergeError` |

## 主要シナリオ
- 例外が正しい親クラスから継承されているかをチェック（`InvalidOptionError → ConfigurationError → CelestialFlowError` のような多重継承チェーンの検証）。
- `field`、`value`、`allowed` などの追加フィールドが保存されているかをチェック。
- デフォルト文言とカスタムエラーメッセージが読み取り可能であるかをチェック。

## 実行方法

```bash
pytest tests/runtime/test_errors.py -v
pytest tests/runtime/test_errors.py -k "invalid_option or connection" -v
pytest tests/runtime/test_errors.py -k "timeout or task_format or termination" -v
```
