# test_executor.py テスト説明

> 📅 最終更新日: 2026/04/22

## テスト目的

`TaskExecutor` の3つの実行モード（`serial` / `thread` / `async`）におけるコア機能を検証します：タスクスケジューリング、結果の正確性、例外処理、リトライメカニズム、重複チェック、成功キャッシュ、および設定バリデーション。`TaskExecutor` は CelestialFlow の最も基本的なタスク実行ユニットであり、その安定性はフレームワーク全体の基盤です。

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestExecutorSerial` | 4 | シリアルモードの基本機能、エラー処理、リトライ、例外フィルタリング |
| `TestExecutorThread` | 1 | スレッドモードの並行処理の正確性 |
| `TestExecutorAsync` | 2 | 非同期モードの基本機能、並行バッチタスク |
| `TestExecutorDuplicateCheck` | 2 | 重複排除の有効化/無効化 |
| `TestExecutorSuccessCache` | 1 | 成功結果のキャッシュ |
| `TestExecutorConfig` | 2 | 不正な設定の遮断、summary フィールドの完全性 |

### 主要テストケースの詳細

#### `test_serial_basic`
- **目的**：シリアルモードでタスクが順次実行され、結果辞書とカウンター統計が正しいことを検証します。
- **入力**：`[1, 2, 3, 4, 5]`、関数 `add_one`
- **アサーション**：`result_dict[x] == x + 1`；`tasks_succeeded == 5`

#### `test_serial_with_errors`
- **目的**：一部のタスクが失敗した場合でも、成功タスクが継続して実行され、エラー情報が正しく記録されることを検証します。
- **入力**：`[1, -1, 2, -2, 3]`、関数 `raise_on_negative`
- **アサーション**：3件成功、2件失敗。失敗結果に例外テキストが含まれること。

#### `test_serial_retry`
- **目的**：設定された例外タイプに対してリトライメカニズムが機能し、最終的な成功が失敗としてカウントされないことを検証します。
- **設計**：`flaky` 関数が最初の2回の呼び出しで `RuntimeError` を発生させ、3回目で成功します。
- **アサーション**：`call_count == 3`（初回1回 + リトライ2回）；`tasks_failed == 0`

#### `test_serial_no_retry_for_unmatched_exception`
- **目的**：設定されていない例外タイプではリトライがトリガーされず、直接失敗としてカウントされることを検証します。
- **設計**：リトライを `RuntimeError` に設定しますが、関数は `ValueError` を発生させます。

#### `test_duplicate_check_enabled`
- **目的**：重複排除を有効にすると、重複入力は1回のみ実行されることを検証します。
- **入力**：`[1, 1, 2, 2, 2, 3]`
- **アサーション**：`tasks_succeeded == 3`、`tasks_duplicated == 3`

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `pytest-asyncio` | 非同期テストサポート |
| `celestialflow.TaskExecutor` | テスト対象 |

## 発生しうる問題と注意事項

### 1. スレッドモードでの結果順序
`test_thread_basic` は結果の正確性のみを検証し、**実行順序は検証しません**。マルチスレッド環境では、タスクの完了順序が入力順序と異なる場合があります。ビジネスロジックが順序に依存する場合は、`process_result()` で明示的に処理する必要があります。

### 2. 非同期テストのイベントループ戦略
`pytest-asyncio` はデフォルトで `function` スコープのイベントループを使用します。大量の非同期テスト（100件以上）を同時に実行すると、イベントループのリソースが枯渇する可能性があります。現在の2つの非同期テストケースではこのリスクはありません。

### 3. `process_result_dict` のキー競合
`process_result_dict()` は元のタスクを辞書キーとして使用します。タスクがハッシュ不可能な型（`list` や `dict` など）の場合、`TypeError` が発生します。現在のテストでは整数のみを使用しているため、この問題はありません。

**推奨事項**：本番環境でタスクがハッシュ不可能なオブジェクトの場合は、カスタム `process_result()` または `get_success_pairs()` を使用してください。

### 4. リトライ時のクロージャ状態
`test_serial_retry` は `nonlocal call_count` を使用して呼び出し回数を追跡します。`thread` モードでは、`call_count` がスレッドセーフなメカニズム（`threading.Lock` など）を使用していない場合、カウントの競合が発生する可能性があります。現在のシリアルテストではこの問題はありませんが、`flaky` を `thread` モードで使用する場合は、`Value` または `Lock` を使用する必要があります。

### 5. `show_progress=False` の必要性
すべてのテストケースで明示的に `show_progress=False` を設定しています。このパラメータを省略すると、TTY のない CI/CD 環境で `tqdm` が文字化けした出力を生成したりブロックしたりする可能性があります。

### 6. 不正モードテストの例外タイプ
`test_invalid_execution_mode` は正確な例外タイプではなく `pytest.raises(Exception)` を使用しています。現在の実装は `ExecutionModeError` を発生させますが、テストの記述が緩やかです。以下のように変更することを推奨します：
```python
with pytest.raises(ExecutionModeError):
    ...
```

## 実行方法

```bash
# すべて実行
pytest tests/test_executor.py -v

# シリアルテストのみ
pytest tests/test_executor.py::TestExecutorSerial -v

# 非同期テストのみ
pytest tests/test_executor.py::TestExecutorAsync -v
```

## パフォーマンス参考値

一般的な開発マシンでの実行時間：
- シリアル、5タスク：`< 10ms`
- スレッド、5タスク：`< 20ms`
- 非同期、20タスク：`< 10ms`

## 関連ファイル

- `src/celestialflow/stage/core_executor.py`：テスト対象の実装
- `src/celestialflow/runtime/core_dispatch.py`：スケジューリングロジック
- `tests/demo_executor.py`：TaskExecutor のデモ/統合テスト（アサーションなし）
