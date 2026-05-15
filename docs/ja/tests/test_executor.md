# test_executor.py テスト説明

> 📅 最終更新日: 2026/05/08

## テスト目的

3つの実行モード（`serial` / `thread` / `async`）における `TaskExecutor` のコア能力を検証します：タスクスケジューリング、結果の正確性、例外処理、リトライメカニズム、重複チェック、成功キャッシュ、設定バリデーション、Observer コールバック。`TaskExecutor` は CelestialFlow の最も基本的なタスク実行単位であり、その安定性はフレームワーク全体の基盤です。

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestExecutorSerial` | 4 | シリアルモード基本機能、エラー処理、リトライ、例外フィルタリング |
| `TestExecutorThread` | 1 | スレッドモード並行処理の正確性 |
| `TestExecutorAsync` | 2 | 非同期モード基本機能、並行バッチタスク |
| `TestExecutorDuplicateCheck` | 2 | 重複チェック有効/無効 |
| `TestExecutorSuccessCache` | 1 | 成功結果キャッシュ |
| `TestExecutorConfig` | 2 | 不正設定の遮断、summary フィールドの完全性 |
| `TestExecutorObserver` | 7 | ライフサイクルコールバック、エラーコールバック、Observer なし、複数 Observer、Observer 削除、CallbackObserver、部分コールバック |

### 主要テストケースの詳細

#### `test_serial_basic`
- **目的**: シリアルモードでタスクが順番に実行され、結果辞書とカウンター統計が正しいことを検証。
- **入力**: `[1, 2, 3, 4, 5]`、関数 `add_one`
- **アサーション**: `result_dict[x] == x + 1`；`tasks_succeeded == 5`

#### `test_serial_with_errors`
- **目的**: 一部のタスクが失敗した場合、成功タスクは実行を継続し、エラー情報が正しく記録されることを検証。
- **入力**: `[1, -1, 2, -2, 3]`、関数 `raise_on_negative`
- **アサーション**: 3個成功、2個失敗；失敗結果に例外テキストを含む。

#### `test_serial_retry`
- **目的**: 設定された例外タイプに対してリトライメカニズムが機能し、最終的に成功したタスクが失敗としてカウントされないことを検証。
- **設計**: `flaky` 関数は最初の2回で `RuntimeError` をスロー、3回目で成功。
- **アサーション**: `call_count == 3`（初回1回 + リトライ2回）；`tasks_failed == 0`

#### `test_observer_lifecycle`
- **目的**: 実行中に Observer が完全なライフサイクルコールバック（start → success × N → finish）を受け取ることを検証。
- **設計**: `RecordingObserver` がすべてのイベントを記録し、イベントタイプと順序を検証。

#### `test_callback_observer`
- **目的**: `CallbackObserver` がコールバック関数を通じてイベントを受け取ることを検証。
- **設計**: `on_task_success` と `on_finish` コールバックを渡し、呼び出し回数を検証。

#### `test_multiple_observers`
- **目的**: 複数の Observer が同時にコールバックを受け取ることを検証。

#### `test_remove_observer`
- **目的**: 削除された Observer がコールバックを受け取らなくなることを検証。

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
# 全テスト実行
pytest tests/test_executor.py -v

# シリアルテストのみ
pytest tests/test_executor.py::TestExecutorSerial -v

# Observer テストのみ
pytest tests/test_executor.py::TestExecutorObserver -v
```

## 関連ファイル

- `src/celestialflow/stage/core_executor.py`: テスト対象の実装
- `src/celestialflow/runtime/core_dispatch.py`: スケジューリングロジック
- `src/celestialflow/observability/core_observer.py`: Observer 基底クラス
- `demo/demo_executor.py`: TaskExecutor のデモスクリプト
