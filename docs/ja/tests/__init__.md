# tests テストパッケージ

> 📅 最終更新日: 2026/06/18

## 役割
`tests/` ディレクトリは CelestialFlow の pytest テストスイートを格納します。`tests/__init__.py` は空ファイルであり、本ページはテストディレクトリ構成の説明を目的とします。

## ディレクトリ構成
- `tests/funnel/`: Inlet / Spout パイプラインの基本動作テスト。
- `tests/graph/`: TaskGraph の構築とスケジューリングテスト。
- `tests/observability/`: 実行状態レポートと注入テスト。
- `tests/persistence/`: sqlite 耐障害永続化、ログ永続化、sqlite ユーティリティテスト。
- `tests/runtime/`: エンベロープ、キュー、ハッシュ、カウンタ、例外、推定テスト。
- `tests/stage/`: TaskStage / TaskExecutor と組み込み Stage のテスト。
- `tests/utils/`: クローンユーティリティとフォーマットユーティリティのテスト。
- `tests/web/`: Web API とサービス統合テスト。
- `tests/conftest.py`: 共通テストヘルパー。
- `tests/__init__.py`: 空ファイル、テストパッケージのマーカー。

## 実行方法

```bash
pytest tests -v
pytest tests/runtime -v
pytest tests/stage -k "executor or stage" -v
```
