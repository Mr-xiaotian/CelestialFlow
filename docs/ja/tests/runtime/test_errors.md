# ランタイム例外テスト (test_errors.py)

> 📅 最終更新日: 2026/07/16

## 役割
`celestialflow.runtime.util_errors` のカスタム例外体系を検証し、例外の継承関係、デフォルトメッセージ、追加フィールドが期待通りであることを確認します。

## カバレッジポイント
- 基本例外：`CelestialFlowError`。
- オプションエラー：`InvalidOptionError`、`ExecutionModeError`、`StageModeError`、`ScheduleModeError`、`LogLevelError`、および各フィールド（`field`、`value`、`allowed`）。
- グラフ構造エラー：`GraphStructureError`、`DuplicateNodeError`、`UnknownNodeError`。
- ランタイムとライフサイクル：`RuntimeStateError`、`InitializationError`、`CelestialFlowTimeoutError`（`TimeoutError` も同時に継承）、`UnconsumedError`。
- タスクとロジック：`TerminationMergeError`。
- 外部依存：`ReporterError`、`RemoteWorkerError`。

## テストカバレッジマトリクス

| 分類 | ケース数 | カバーする例外 |
|------|---------|--------------|
| 基本例外 | 1 | `CelestialFlowError` |
| 設定とオプション | 8 | `ConfigurationError`、`InvalidOptionError`（カスタムプレフィックス含む）、`ExecutionModeError`（カスタムモード含む）、`StageModeError`、`LogLevelError`、`ScheduleModeError` |
| グラフ構造 | 3 | `GraphStructureError`、`DuplicateNodeError`、`UnknownNodeError` |
| ランタイムとライフサイクル | 4 | `RuntimeStateError`、`InitializationError`、`CelestialFlowTimeoutError`、`UnconsumedError` |
| 外部サービスと通信 | 2 | `RemoteWorkerError`、`ReporterError` |
| タスクとロジック | 1 | `TerminationMergeError` |

## 主要シナリオ
- 例外が正しい親クラスから継承されているかをチェック（`InvalidOptionError → ConfigurationError → CelestialFlowError` のような多重継承チェーンの検証）。
- `field`、`value`、`allowed` などの追加フィールドが保存されているかをチェック。
- デフォルト文言とカスタムエラーメッセージが読み取り可能であるかをチェック。

## 実行方法

```bash
pytest tests/runtime/test_errors.py -v
pytest tests/runtime/test_errors.py -k "invalid_option or execution_mode" -v
pytest tests/runtime/test_errors.py -k "timeout or termination or graph_structure" -v
```
