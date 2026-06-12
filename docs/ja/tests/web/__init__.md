# web テストパッケージ

> 📅 最終更新日: 2026/06/11

## 役割
`tests/web/` は CelestialFlow Web 層のインターフェースとページ統合動作をカバーし、状態スナップショットの分離、状態プッシュ/プル、設定プッシュ、タスク注入、エラーページングフィルタリング、フロントエンド静的リソース連携が安定していることを確認します。

## 含まれるテストファイル
- `conftest.py`: `web_server` および `client` fixture を提供。
- `test_server.py`: スナップショット分離、ダッシュボードトップページ、設定 API、状態同期、タスク注入、エラーページングなどの Web API 統合テストをカバー。

## 実行方法

```bash
pytest tests/web -v
pytest tests/web/test_server.py -v
```
