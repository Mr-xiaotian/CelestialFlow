# オブザーバーテスト (test_observer.py)

> 📅 最終更新日: 2026/06/22

## 役割
`celestialflow.observability` モジュールのオブザーバー（Observer）機構を検証し、タスク実行ライフサイクルの各キーノードでコールバックが正しくトリガーされることを確認します。

## コアテスト対象
- `BaseObserver`: オブザーバー基底クラス。
- `TaskExecutor`: 観測対象のタスク実行者。

## 主要テストフロー
1. **ライフサイクルコールバック**: `on_start` から `on_finish` までの完全なイベントフローを検証。タスク成功、失敗、新規タスクなどのイベントを含む。
2. **マルチオブザーバーサポート**: 複数のオブザーバーを同一の実行者に同時にマウントし、独立してイベントを受信できることを検証。
3. **動的管理**: オブザーバーの動的な追加と削除ロジックを検証。

## テストの重点
- **イベント順序**: `on_start` が最初にトリガーされ、`on_finish` が最後にトリガーされることを確認。
- **失敗キャプチャ**: タスクが例外をスローしたときに `on_task_fail` が正しく呼び出され、カウントが正確であることを検証。
- **デフォルト動作**: オーバーライドされていないメソッドは基底クラスの空実装を通り、例外が発生しないことを検証。

## 重要な詳細
- `RecordingObserver` や `CountObserver` などの Mock クラスを使用してイベントを収集・検証します。
- `test_remove_observer` はアンバインド後のオブザーバーが副作用を生じないことを確認します。

## 実行方法

```bash
# すべて実行
pytest tests/observability/test_observer.py -v

# ライフサイクルコールバックテストのみ実行
pytest tests/observability/test_observer.py -k "lifecycle" -v

# 動的管理テストのみ実行（オブザーバーの追加/削除）
pytest tests/observability/test_observer.py -k "observer_remove" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|------|------|
| `TestExecutorObserver` | ~2s（タスク実行を含む） |

## 注意事項
- オブザーバーパターンはフレームワークの監視、ログ、プログレスバーの基盤です。
- テストコードは `tests/observability/test_observer.py` にあります。
