# test_executor.py テスト説明

> 📅 最終更新日: 2026/05/08

## テスト目標

`TaskExecutor` の3つの実行モード（`serial` / `thread` / `async`）におけるコア機能を検証：タスクスケジューリング、結果の正確性、例外処理、リトライ機構、重複チェック、成功キャッシュ、設定検証、Observer コールバック。

## テスト範囲

| テストクラス | テスト数 | カバレッジ |
|-------------|---------|-----------|
| `TestExecutorSerial` | 4 | シリアルモードの基本機能、エラー処理、リトライ、例外フィルタリング |
| `TestExecutorThread` | 1 | スレッドモードの並行正確性 |
| `TestExecutorAsync` | 2 | 非同期モードの基本機能、並行バッチタスク |
| `TestExecutorDuplicateCheck` | 2 | 重複チェックの有効/無効 |
| `TestExecutorSuccessCache` | 1 | 成功結果キャッシュ |
| `TestExecutorConfig` | 2 | 不正設定の検出、summary フィールドの完全性 |
| `TestExecutorObserver` | 7 | ライフサイクルコールバック、エラーコールバック、observer なし、複数 observer、observer 削除、CallbackObserver、部分コールバック |

### 主要テスト詳細

#### `test_observer_lifecycle`
- **目標**: observer が実行中に完全なライフサイクルコールバック（start → success × N → finish）を受け取ることを検証。

#### `test_callback_observer`
- **目標**: `CallbackObserver` がコールバック関数でイベントを受け取ることを検証。

#### `test_multiple_observers`
- **目標**: 複数の observer が同時にコールバックを受け取ることを検証。

#### `test_remove_observer`
- **目標**: observer 削除後にコールバックを受け取らないことを検証。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `pytest-asyncio` | 非同期テストサポート |
| `celestialflow.TaskExecutor` | テスト対象 |
| `celestialflow.BaseObserver` | Observer 基底クラス |
| `celestialflow.CallbackObserver` | コールバック式 Observer |

## 実行方法

```bash
pytest tests/test_executor.py -v
pytest tests/test_executor.py::TestExecutorObserver -v
```

## 関連ファイル

- `src/celestialflow/stage/core_executor.py`: テスト対象実装
- `src/celestialflow/runtime/core_dispatch.py`: ディスパッチロジック
- `src/celestialflow/observability/core_observer.py`: Observer 基底クラス
- `demo/demo_executor.py`: TaskExecutor のデモスクリプト
