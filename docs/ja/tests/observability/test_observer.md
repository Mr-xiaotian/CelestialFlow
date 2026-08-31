# オブザーバーテスト (test_observer.py)

> 📅 最終更新日: 2026/08/26

## 役割
`celestialflow.observability` モジュールのオブザーバー（Observer）機構を検証し、タスク実行ライフサイクルの各キーノードでコールバックが正しくトリガーされることを確認します。

## コアテスト対象
- `BaseObserver`: オブザーバー基底クラス。
- `TaskExecutor`: 観測対象のタスク実行者。

## テストカバレッジマトリックス

| テストクラス | ケース | カバレッジ対象 |
|------------|------|--------------|
| `TestExecutorObserver` | `test_observer_lifecycle` | 完全なライフサイクルコールバック：`on_start` が出現、`on_task_success` コールバック回数がタスク数（3 回）と一致、`on_finish` が最後にトリガー |
| `TestExecutorObserver` | `test_observer_with_errors` | 失敗コールバック：3 タスク中 2 成功 1 失敗、成功/失敗カウントが正確 |
| `TestExecutorObserver` | `test_no_observer_works` | observer 未マウントでもエグゼキュータは正常に動作し、カウントに影響しない |
| `TestExecutorObserver` | `test_multiple_observers` | 複数の observer を同時にマウント、それぞれ独立に同一コールバックを受信 |
| `TestExecutorObserver` | `test_remove_observer` | `remove_observer()` でアンバインド後はいかなるコールバックも受信しない |

## テストの重点
- **イベント順序**: `on_start` が最初にトリガーされ、`on_finish` が最後にトリガーされることを確認。
- **失敗キャプチャ**: タスクが例外をスローしたときに `on_task_fail` が正しく呼び出され、カウントが正確であることを検証。
- **オブザーバー組み合わせ**: 複数 observer のマウントとアンバインド（除去後の副作用なし）を検証。

## 重要な詳細
- `RecordingObserver`、`CountObserver`、`Counter` などの Mock クラスを使用してイベントを収集・検証します。
- `RecordingObserver` は `on_start` / `on_task_success` / `on_task_fail` / `on_task_duplicate` / `on_tasks_added` / `on_finish` をオーバーライドし、`on_task_success` と `on_task_fail` はデフォルトのカウント引数 `count=1` を持ちます。
- `test_remove_observer` はアンバインド後のオブザーバーが副作用を生まないことを確認します。

## 実行方法

```bash
# 全部実行
pytest tests/observability/test_observer.py -v

# ライフサイクルコールバックテストのみ実行
pytest tests/observability/test_observer.py -k "lifecycle" -v

# 動的管理テストのみ実行（オブザーバーの追加/削除）
pytest tests/observability/test_observer.py -k "observer_remove" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|---------|
| `TestExecutorObserver` | ~2s（タスク実行を含む） |

## 注意事項
- オブザーバーパターンはフレームワークの監視、ログ、プログレスバーの基盤です。
- テストコードは `tests/observability/test_observer.py` にあります。
