# tests/runtime/test_errors.py

> 📅 最終更新日: 2026/11/13

## 役割
`celestialflow.runtime.util_errors` のカスタム例外体系を検証し、例外の継承関係、デフォルトメッセージ、追加フィールドが期待通りであることを確認します。

## カバレッジポイント
- 基本例外：`CelestialFlowError`。
- 設定とオプションエラー：`ConfigurationError`、`InvalidOptionError`（`field`、`value`、`allowed` フィールドとカスタムプレフィックスを含む）。
- グラフ構造エラー：`GraphStructureError`、`DuplicateNodeError`、`UnknownNodeError`。
- ランタイムとライフサイクル：`RuntimeStateError`、`InitializationError`、`CelestialFlowTimeoutError`（`TimeoutError` も同時に継承）、`UnconsumedError`。
- タスクとロジック：`TerminationMergeError`。
- 外部依存：`ReporterError`、`RemoteWorkerError`。

## テストカバレッジマトリクス

| 分類 | ケース数 | カバーする例外 |
|------|---------|--------------|
| 基本例外 | 1 | `CelestialFlowError` |
| 設定とオプション | 6 | `ConfigurationError`、`InvalidOptionError`（カスタムプレフィックス、`execution_mode` / `graph_mode` / `log_level` などの不正フィールド値を含む） |
| グラフ構造 | 3 | `GraphStructureError`、`DuplicateNodeError`、`UnknownNodeError` |
| ランタイムとライフサイクル | 4 | `RuntimeStateError`、`InitializationError`、`CelestialFlowTimeoutError`、`UnconsumedError` |
| 外部サービスと通信 | 2 | `RemoteWorkerError`、`ReporterError` |
| タスクとロジック | 1 | `TerminationMergeError` |
| **合計** | **17** | |

> **本ファイルでカバーしない例外クラス**：`CallableParameterKindError`（現在どのテストも直接インスタンス化していない）、`NodeNotFoundError`（`tests/graph/test_graph.py` がカバー）、`InvalidStructureError`（`tests/graph/test_structure.py` がカバー）、`PersistedError`（`tests/node/test_nodes.py` がカバー）。本ファイルは上表の 13 個の例外クラスについて、構築・継承・メッセージの契約のみを保証します。

## 主要シナリオ
- 例外が正しい親クラスから継承されているかをチェック（`InvalidOptionError → ConfigurationError → CelestialFlowError` のような多重継承チェーンの検証）。
- `field`、`value`、`allowed` などの追加フィールドが保存されているかをチェック；`allowed` は `tuple` に正規化されます。
- デフォルトメッセージの形式 `"{prefix} {field}: {value}. Valid options are {allowed}."`、および `prefix="Bad"` のときのカスタムプレフィックスをチェック。
- 異なる不正フィールド値（`execution_mode`、`graph_mode`、`log_level` など）がすべて `InvalidOptionError` によって統一的に処理され、フィールド情報が公開されることをチェック。
- デフォルト文言とカスタムエラーメッセージが読み取り可能であるかをチェック。

## 実行方法

```bash
pytest tests/runtime/test_errors.py -v
pytest tests/runtime/test_errors.py -k "invalid_option or execution_mode" -v
pytest tests/runtime/test_errors.py -k "timeout or termination or graph_structure" -v
```
