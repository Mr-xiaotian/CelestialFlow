# web テストパッケージ

> 📅 最終更新日: 2026/06/05

## 目的

組み込み Web サーバーと HTTP 監視エンドポイントのテストを索引化します。

## 主要ポイント

- サーバー統合と request/response の挙動を扱います。
- 静的アセット文書をバックエンド側テストで補完します。

## 実行方法

```bash
pytest tests/web -v
pytest tests/web -k "routes or server" -v
```
