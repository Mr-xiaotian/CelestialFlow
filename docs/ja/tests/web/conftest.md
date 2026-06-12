# Web テスト設定 (conftest.py)

> 📅 最終更新日: 2026/05/23

## 役割
`tests/web` ディレクトリのテストケースに Web サーバーと HTTP クライアントの Pytest Fixture を提供し、実際のフロントエンド・バックエンド対話環境をシミュレートします。

## コア Fixture
- `web_server`:
  - **機能**: デフォルト設定の `TaskWebServer` インスタンスを初期化。
  - **スコープ**: 各テスト関数実行前に新しいインスタンスを作成。
- `client`:
  - **機能**: `FastAPI.testclient.TestClient` に基づき同期 HTTP クライアントを作成。
  - **依存**: `web_server` fixture に依存し、その内部の `app` インスタンスに直接アクセス。

## 使用例
```python
def test_api(client):
    response = client.get("/api/endpoint")
    assert response.status_code == 200
```

## 注意事項
- テストは FastAPI 組み込みの TestClient を使用し、実際のポートリスニングを開始しないため、実行効率が高くポート競合のリスクがありません。
- 関連実装は `src/celestialflow/web/core_server.py` にあります。
