# カスタム例外クラステスト (test_errors.py)

> 📅 最終更新日: 2026/05/28

## 目的

`celestialflow.runtime.util_errors` 内のすべてのカスタム例外クラスのインスタンス化、継承関係、メッセージの完全性を検証し、フレームワークの各モジュールが期待される型の例外を正しく送出およびキャッチできることを確認します。

## コアテスト対象

すべてのカスタム例外クラスを 4 つのグループに分類：

| グループ | 例外クラス | 説明 |
|----------|------------|------|
| 基本 | `CelestialFlowError` | フレームワークの全例外の基底クラス |
| 設定とオプション | `ConfigurationError`, `InvalidOptionError`, `ExecutionModeError`, `StageModeError`, `LogLevelError`, `ScheduleModeError` | パラメータ検証とモード設定エラー |
| グラフ構造 | `GraphStructureError`, `DuplicateNodeError`, `UnknownNodeError` | DAG トポロジとノード検証エラー |
| ランタイムと外部 | `RuntimeStateError`, `InitializationError`, `CelestialFlowTimeoutError`, `UnconsumedError`, `RemoteWorkerError`, `ReporterError`, `CelestialTreeConnectionError`, `TaskFormatError`, `TerminationMergeError` | ライフサイクル、外部サービス、タスクロジックエラー |

## 主要テストシナリオ

- **基底クラスのインスタンス化**：`CelestialFlowError("something went wrong")` は `Exception` のサブクラス
- **継承チェーンの検証**：`ExecutionModeError` は `CelestialFlowError` と `InvalidOptionError` の両方のインスタンス
- **フィールドの完全性**：`InvalidOptionError` の `field`、`value`、`allowed` 属性が正しく設定される
- **有効値の列挙**：`ExecutionModeError`、`StageModeError`、`LogLevelError` などの `valid_modes` / `valid_levels` が正しい列挙値を含む
- **デフォルトメッセージ**：`CelestialTreeConnectionError()` の引数なし構築で `"CelestialTreeClient"` を含むメッセージを生成
- **`PersistedErrorRecord` はこのファイルではテストされない**（この型は `test_types.py` でカバー）

## 実行方法

```bash
# 全実行
pytest tests/utils/test_errors.py -v

# 設定例外テストのみ
pytest tests/utils/test_errors.py -k "config or option or execution or stage or log or schedule" -v

# グラフ構造例外テストのみ
pytest tests/utils/test_errors.py -k "graph or duplicate or unknown" -v

# ランタイム例外テストのみ
pytest tests/utils/test_errors.py -k "runtime or init or timeout or unconsumed" -v
```

## パフォーマンス参考

| テストクラス | 所要時間 |
|--------------|----------|
| `TestUtilErrors` | ~0.05s |

## 重要な詳細

- 例外継承階層は `CelestialFlowError → ConfigurationError → InvalidOptionError → {具象エラー}` として設計されており、柔軟なキャッチレベルを確保します。
- `InvalidOptionError` は `allowed` を自動的にタプルに変換し、説明的なエラーメッセージにフォーマットします。

## 注意事項

- フレームワークが送出するすべての例外は `CelestialFlowError` を継承し、ユーザーが統一的にキャッチできるようにする必要があります。
- 関連実装は `src/celestialflow/runtime/util_errors.py` にあります。
