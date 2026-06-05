# ログ永続化テスト (test_log.py)

> 📅 最終更新日: 2026/06/05

## 目的

グラフ、リトライ、ステージライフサイクルのログがログファイルへ出力されることを検証します。

## 主要ポイント

- INFO と WARNING の両方の内容を確認します。
- 実ログを汚さないよう一時ディレクトリを使います。

## 実行方法

```bash
pytest tests/persistence/test_log.py -v
pytest tests/persistence/test_log.py -k "log_persistence" -v
```
