# persistence テストパッケージ

> 📅 最終更新日: 2026/08/26

## 役割
`tests/persistence/` はライフサイクル永続化、ログ記録、sqlite ユーティリティ関数の3つの永続化パスをカバーし、Inlet / Spout ペアコンポーネントがバックグラウンドスレッドで正しくディスクに書き込む、またはログをバッチフラッシュできることを検証します。

## 含まれるテストファイル
- `test_lifecycle.py`: タスクライフサイクルイベントの sqlite 永続化（`LifecycleInlet` / `LifecycleSpout`）。
- `test_log.py`: ログレコードのテキストファイルへのバッチ書き込み（`LogInlet` / `LogSpout`）。
- `test_splite.py`: sqlite ユーティリティ関数（テーブル作成、CRUD、状態遷移、グループ読み込み）。
- `test_scope.py`: `funnel_scope()` コンテキストマネージャによるグローバル spout のライフサイクル管理。

## 実行方法

```bash
pytest tests/persistence -v
pytest tests/persistence -k "lifecycle or log or splite" -v
```
