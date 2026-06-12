# runtime テストパッケージ

> 📅 最終更新日: 2026/06/05

## 役割
`tests/runtime/` は CelestialFlow のランタイムインフラストラクチャ（タスクエンベロープ、キュー、ハッシュ、カウンタ、例外型、残り時間推定を含む）をカバーし、スケジューリング層と Stage 層の基盤を保証します。

## 含まれるテストファイル
- `test_dispatch.py`: スケジューリングループとディスパッチロジック。
- `test_envelope.py`: `TaskEnvelope` の属性とハッシュ動作。
- `test_errors.py`: カスタム例外体系。
- `test_estimators.py`: 経過時間と残り時間の推定アルゴリズム。
- `test_hash.py`: `make_hashable` と `object_to_hash`。
- `test_metrics.py`: カウンタと実行メトリクス集計。
- `test_queue.py`: タスク入出力キュー。
- `test_types.py`: 各種ランタイム値オブジェクト、列挙型、コンテキストラッパー。

## 実行方法

```bash
pytest tests/runtime -v
pytest tests/runtime -k "hash or envelope or estimators" -v
```
