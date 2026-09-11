# tests/ テスト概要

> 📅 最終更新日: 2026/09/09

## 説明

本ディレクトリは `tests/` 配下の pytest テストセットの中国語説明ドキュメントを収集し、異なるモジュールのカバレッジ範囲、実行方法、リグレッションリスクポイントを素早く特定できるようにします。

`demo/` とは異なり、ここでは「機能が正しいかどうか」に焦点を当てます。`bench/` とは異なり、パフォーマンスではなく、動作制約、境界ケース、プロトコル整合性に関心を置きます。

## 推奨読書順序

テストセットを初めて見る方は、以下の順序で読むことを推奨します：

1. `conftest.md`：まずテストヘルパーと共有初期化の説明を確認
2. `runtime/`：基本型、キュー、例外、スケジューリングプリミティブのカバレッジ範囲を理解
3. `graph/`：グラフ構造、タスクトポロジのコアテストを理解
4. `observability/`：最後に Reporter とレポートチェーンの統合テストを確認

## ドキュメントインデックス

### トップレベルエントリ

| ドキュメント | 説明 |
|------|------|
| `conftest.md` | グローバル fixture、テストヘルパー、共有初期化の説明 |

### サブディレクトリ説明

| ドキュメント | 説明 |
|------|------|
| `funnel/test_inlet.md` / `test_spout.md` | Inlet / Spout パイプライン関連テスト |
| `graph/test_graph.md` など | `TaskGraph`、トポロジ分析、構造エクスポート関連テスト |
| `observability/test_observer.md` / `test_reporter.md` | オブザーバー、Reporter、注入、レポート関連テスト |
| `persistence/test_lifecycle.md` など | ライフサイクル / ログ / sqlite ユーティリティなど永続化関連テスト |
| `runtime/test_envelope.md` など | キュー、エンベロープ、例外、推定器、カウンターなどの基本ランタイムテスト |
| `benchmark/test_benchmark.md` / `test_clone.md` | `benchmark_graph` / `benchmark_executor` ベンチマークテストと clone ヘルパーのテスト |

## 使用方法

プロジェクトルートからモジュール別に実行できます：

```bash
pytest tests -v
pytest tests/runtime -v
pytest tests/graph -v
pytest tests/observability -v
```

キーワードでフィルタすることもできます：

```bash
pytest tests -k "executor or graph or reporter" -v
```

## 読み方

以下の方法でこれらのドキュメントを活用することを推奨します：

- あるモジュールが「テストされているか」を知りたい場合：まず対応するサブディレクトリの `test_*.md` を確認
- ある具体的な動作が「どのようにテストされているか」を知りたい場合：対応する `test_*.md` を確認（サブディレクトリには `__init__.md` は存在しない）
- プロトコル変更の影響範囲を特定したい場合：`graph/`、`runtime/`、`persistence/`、`observability/` のドキュメント群を優先的に確認

## 注意事項

1. 一部のテストは一時ファイル、sqlite、イベントキュー、または HTTP レポートチェーンに依存します。実行環境のジッターは実行時間に影響する可能性がありますが、アサーション結果には影響しません。
2. 本番プロトコルが変更された場合、テストドキュメントは通常 `src/`、`demo/` と共に同期更新する必要があります。
3. 現在の変更を素早く検証したいだけの場合は、変更ディレクトリに最も近いテストサブセットを優先的に実行し、常に全量テストを実行する必要はありません。
4. 本ディレクトリのサブディレクトリ（`runtime/`、`graph/`、`funnel/`、`observability/`、`persistence/`、`benchmark/`）は **いずれも `__init__.py` を持たない**ため、対応する `__init__.md` も存在しません。
