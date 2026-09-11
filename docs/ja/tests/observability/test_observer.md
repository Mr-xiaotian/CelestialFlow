# オブザーバーテスト (test_observer.py)

> 📅 最終更新日: 2026/09/09

## 役割
`celestialflow` パッケージからエクスポートされる `BaseObserver` と `TaskExecutor` の間のコールバック契約を検証し、タスク実行ライフサイクルにおけるキーノードで `BaseObserver` のオーバーライドメソッドが正しくトリガーされることを確認します。

## コアテスト対象
- `BaseObserver`: `celestialflow.observability` 由来のオブザーバー基底クラス。`on_start` / `on_task_success` / `on_task_fail` / `on_task_duplicate` / `on_tasks_added` / `on_finish` などのコールバックフックを提供。
- `TaskExecutor`: `celestialflow.node` 由来の被観測タスクエグゼキュータ（テストではトップレベル `celestialflow` パッケージからインポート）。

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
- `RecordingObserver` は `on_start` / `on_task_success` / `on_task_fail` / `on_task_duplicate` / `on_tasks_added` / `on_finish` をオーバーライドし、`on_task_success` と `on_task_fail` はデフォルトのカウント引数 `count=1` を明示的に宣言します。
- `CountObserver` は `on_task_success` / `on_task_fail` のみをオーバーライドし、`count` フィールドを累積することで集約統計を実現します。
- `test_remove_observer` は `executor.remove_observer(observer)` でアンバインド後に再度 `run` を呼び出し、`observer.count == 0` をアサートします。
- すべてのケースは `execution_mode="serial"` モードを使用しており、イベントを順序通りにアサートできます。

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
