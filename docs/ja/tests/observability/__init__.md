# observability テストパッケージ

> 📅 最終更新日: 2026/06/22

## 役割
`tests/observability/` は実行状態観測とタスク注入/レポート機構をカバーし、`BaseObserver` のライフサイクルコールバックおよび `TaskReporter` のタスク注入とエラープッシュ動作が期待通りであることを確認します。

## 含まれるテストファイル
- `test_observer.py`: Observer ライフサイクルコールバック、マルチオブザーバーサポート、動的管理をカバー。
- `test_reporter_injection.py`: `TaskReporter._pull_and_inject_tasks()` のノードマッピング注入とログ記録ロジックをカバー。

## 実行方法

```bash
pytest tests/observability -v
pytest tests/observability/test_observer.py -v
pytest tests/observability/test_reporter_injection.py -v
```
