# Web サービス API テスト (test_server.py)

> 📅 最終更新日: 2026/06/11

## 役割
`celestialflow.web.core_server` が提供する RESTful API を検証し、Web ダッシュボードがグラフ状態を正しく表示し、設定を取得し、タスクを注入し、エラーログを閲覧できることを確認するとともに、スナップショットデータの分離性を検証します。

## コアテスト対象
- `TaskWebServer`: FastAPI ベースの監視・対話サーバー。

## 主要テストシナリオ

### スナップショット分離
- `test_store_snapshot_methods_return_isolated_copies`: server の各スナップショットインターフェースがディープコピーを返し、戻り値を変更しても内部 store に影響しないことを検証。

### 静的リソースレンダリング
- `test_index_page`: トップページ `/` が `dashboard` コンテナを含む HTML ページを正しく返すことを検証。

### 設定取得
- `test_config_api`: フロントエンドが必要とする実行時パラメータ（リフレッシュ頻度、テーマなど）が正しく取得できることを検証。

### 状態同期 (Rev 機構)
- `test_status_push_pull`:
  - `push_status` がスナップショットを正常に保存できることを検証。
  - `pull_status` が増分更新をサポートすること：`known_rev` がサーバーの現在バージョンと一致する場合、帯域節約のために空データを返すことを検証。

### タスク注入
- `test_task_injection`: POST インターフェースで注入されたタスクが正しく一時保存され、スケジューラが GET インターフェースで消費し、消費後にクリアされることを検証。
- `test_task_injection_overwrites_tasklist_per_node`: 新しい push がノードごとにタスクリストを更新し、追記ではないことを検証。
- `test_task_injection_requires_tasklist_mapping`: 不正な payload（非リスト値）が 422 を返すことを検証。

### エラー管理
- `test_errors_pagination`:
  - エラーレコードの一括プッシュを検証。
  - ページングロジックを検証：`total_pages`、`total`、現在ページのデータ量をチェック。
  - ノード（`node`）によるフィルタリングロジックを検証。
  - キーワード（`keyword`）によるフィルタリングロジックを検証。
  - ソート（`sort_order`）：`newest` と `oldest` の 2 種類をサポートすることを検証。

## テストの重点
- **Rev バージョン管理**: フロントエンドのリフレッシュロジックの効率性を確保し、冗長なデータ転送を防止。
- **ページング正確性**: バックエンドのエラーレコード処理時のオフセット計算を検証。
- **タスク一貫性**: 注入されたタスクがプル消費後に正しくクリアされ、重複処理を防止することを確認。
- **スナップショット分離**: フロントエンドが取得したデータが内部状態の突然変異によって不整合を起こさないことを確認。

## 実行方法

```bash
# すべて実行
pytest tests/web/test_server.py -v

# 状態同期テストのみ実行
pytest tests/web/test_server.py -k "status" -v

# タスク注入テストのみ実行
pytest tests/web/test_server.py -k "injection" -v

# エラー管理テストのみ実行
pytest tests/web/test_server.py -k "errors" -v

# 設定取得テストのみ実行
pytest tests/web/test_server.py -k "config" -v
```

## 重要な詳細
- `FastAPI TestClient` を使用してリクエストをシミュレートし、実際のポートリスニングは開始しません。
- スナップショット分離テストは `web_server` fixture（`conftest.py` が提供）を直接操作し、その他のテストは `client` fixture を使用します。
- テストは各関数実行前に新しい server インスタンスを作成します。

## 注意事項
- Web サービスは CelestialFlow の可視化ウィンドウです。
- 関連実装は `src/celestialflow/web/core_server.py` にあります。
