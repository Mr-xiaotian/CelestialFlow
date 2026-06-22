# persistence テストパッケージ

> 📅 最終更新日: 2026/06/22

## 役割
`tests/persistence/` はエラー耐障害性、ログ記録、sqlite ユーティリティ関数の3つの永続化パスをカバーし、Inlet / Spout ペアコンポーネントがバックグラウンドスレッドで正しくディスクに書き込み、またはログをバッチフラッシュできることを検証します。

## 含まれるテストファイル
- `test_fallback.py`: エラーと成功結果の sqlite 永続化（`FallbackInlet` / `FallbackSpout`）。
- `test_log.py`: ログレコードのテキストファイルへのバッチ書き込み（`LogInlet` / `LogSpout`）。
- `test_splite.py`: sqlite ユーティリティ関数（テーブル作成、CRUD、状態マイグレーション、グループ読み込み）。

## 実行方法

```bash
pytest tests/persistence -v
pytest tests/persistence -k "fallback or log or splite" -v
```
